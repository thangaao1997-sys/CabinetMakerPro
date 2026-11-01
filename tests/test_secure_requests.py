import copy
import tempfile
import unittest
from pathlib import Path

from core.command_center import plan_request
from core.secure_requests import (
    EnvelopeError, SQLiteNonceLedger, sign_payload, verify_envelope,
)

SECRET = bytes(range(32))
PAYLOAD = {
    "request_id": "IDEA-SEC-1",
    "text": "Tạo tủ bếp rộng 600 mm sâu 560 mm cao 820 mm",
    "target_model_locked": False,
}


class SignedRequestsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.file = Path(self.directory.name) / "nonce-ledger.db"
        self.ledger = SQLiteNonceLedger(self.file)
        self.ts = 1_800_000_000
        self.env = sign_payload(PAYLOAD, SECRET, issued_at=self.ts,
                                nonce="ab" * 16)

    def verify(self, envelope=None, ledger=None, now=None):
        return verify_envelope(
            self.env if envelope is None else envelope,
            SECRET, self.ledger if ledger is None else ledger,
            now=self.ts if now is None else now
        )

    def test_valid_signature(self):
        self.assertEqual(self.verify()["request_id"], "IDEA-SEC-1")

    def test_tampered_text(self):
        env = copy.deepcopy(self.env)
        env["payload"]["text"] += " xuất CNC"
        with self.assertRaises(EnvelopeError): self.verify(env)

    def test_tampered_lock(self):
        env = copy.deepcopy(self.env)
        env["payload"]["target_model_locked"] = True
        with self.assertRaises(EnvelopeError): self.verify(env)

    def test_expired(self):
        with self.assertRaises(EnvelopeError): self.verify(now=self.ts+301)

    def test_future(self):
        with self.assertRaises(EnvelopeError): self.verify(now=self.ts-61)

    def test_replay_same_ledger(self):
        self.verify()
        with self.assertRaises(EnvelopeError): self.verify()

    def test_replay_across_ledger_instances(self):
        self.verify()
        with self.assertRaises(EnvelopeError):
            self.verify(ledger=SQLiteNonceLedger(self.file))

    def test_short_secret_rejected(self):
        with self.assertRaises(EnvelopeError):
            sign_payload(PAYLOAD, b"123", issued_at=self.ts)

    def test_unknown_envelope_field_rejected(self):
        env = {**self.env, "execute_cnc": True}
        with self.assertRaises(EnvelopeError): self.verify(env)

    def test_missing_ledger_rejected(self):
        with self.assertRaises(EnvelopeError):
            verify_envelope(self.env, SECRET, None, now=self.ts)

    def test_locked_plan_still_blocked_when_signed(self):
        locked_payload = {**PAYLOAD, "target_model_locked": True}
        env = sign_payload(locked_payload, SECRET, issued_at=self.ts,
                           nonce="cd" * 16)
        data = self.verify(env)
        plan = plan_request(data["text"], data["request_id"],
                            data["target_model_locked"])
        self.assertEqual(plan["status"], "blocked_locked_design")
        self.assertFalse(plan["model_write_allowed"])

    def test_unsigned_request_rejected(self):
        env = {k:v for k,v in self.env.items() if k!="signature"}
        with self.assertRaises(EnvelopeError): self.verify(env)

    def test_boolean_timestamp_rejected(self):
        env = {**self.env, "issued_at": True}
        with self.assertRaises(EnvelopeError): self.verify(env)

    def test_payload_type_rejected(self):
        with self.assertRaises(EnvelopeError):
            sign_payload({**PAYLOAD, "target_model_locked": "false"}, SECRET,
                         issued_at=self.ts)

    def test_signature_only_authenticates(self):
        payload = self.verify()
        result = plan_request(payload["text"], payload["request_id"],
                              payload["target_model_locked"])
        self.assertFalse(result["model_write_allowed"])
        self.assertFalse(result["manufacturing_approved"])


if __name__ == "__main__":
    unittest.main()
