import json
import tempfile
import unittest
from pathlib import Path

from core.secure_preview import process_signed_file
from core.secure_requests import EnvelopeError, sign_payload

SECRET=bytes(range(32))
PAYLOAD={"request_id":"SIGNED-PREVIEW-001",
         "text":"Tạo tủ bếp rộng 600 mm sâu 560 mm cao 820 mm",
         "target_model_locked":False}


class SignedPreviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.path=self.root/"command.json"
        self.ledger=self.root/"used.db"
        self.ts=1_800_000_000

    def write(self,payload):
        signed=sign_payload(payload,SECRET,issued_at=self.ts,
                            nonce="ef"*16)
        self.path.write_text(json.dumps(signed),encoding="utf-8")

    def process(self):
        return process_signed_file(self.path,SECRET,self.ledger,now=self.ts)

    def test_signed_draft(self):
        self.write(PAYLOAD)
        result=self.process()
        self.assertTrue(result["authenticated"])
        self.assertEqual(result["execution_mode"],"preview_only")
        self.assertEqual(result["plan"]["status"],"draft_preview_ready")
        self.assertFalse(result["plan"]["model_write_allowed"])

    def test_replay_fails(self):
        self.write(PAYLOAD)
        self.process()
        with self.assertRaises(EnvelopeError): self.process()

    def test_locked_target(self):
        self.write({**PAYLOAD,"target_model_locked":True})
        result=self.process()
        self.assertEqual(result["plan"]["status"],"blocked_locked_design")

    def test_wrong_extension(self):
        self.write(PAYLOAD)
        dst=self.root/"command.txt"
        self.path.rename(dst)
        with self.assertRaises(EnvelopeError):
            process_signed_file(dst,SECRET,self.ledger,now=self.ts)


if __name__=="__main__":
    unittest.main()
