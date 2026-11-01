"""Read-only signed file-drop preview. Not a server, not a CNC exporter."""
import argparse
import json
import os
from pathlib import Path

from .command_center import plan_request
from .secure_requests import EnvelopeError, SQLiteNonceLedger, verify_envelope

MAX_FILE_BYTES = 128_000


def process_signed_file(path, secret, ledger_path, *, now=None):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.suffix.lower() != ".json":
        raise EnvelopeError("Expected a regular local JSON envelope file")
    if path.stat().st_size > MAX_FILE_BYTES:
        raise EnvelopeError("Signed file exceeds maximum allowed size")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise EnvelopeError("Malformed JSON envelope") from exc
    payload = verify_envelope(data, secret, SQLiteNonceLedger(ledger_path),
                              now=now)
    plan = plan_request(payload["text"], payload["request_id"],
                        payload["target_model_locked"])
    return {
        "schema_version": "ai-idea.signed-preview.v1",
        "authenticated": True,
        "execution_mode": "preview_only",
        "plan": plan,
    }


def main():
    parser = argparse.ArgumentParser(description="AI IDEA signed offline preview")
    parser.add_argument("--input", required=True, help="Signed JSON envelope file")
    parser.add_argument("--ledger", required=True, help="Local SQLite nonce ledger")
    args = parser.parse_args()
    key_hex = os.environ.get("AI_IDEA_SHARED_KEY_HEX")
    if key_hex is None:
        parser.error("Missing AI_IDEA_SHARED_KEY_HEX (do not print the key)")
    try:
        secret = bytes.fromhex(key_hex)
        result = process_signed_file(args.input, secret, args.ledger)
    except (EnvelopeError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if result["plan"]["status"] == "draft_preview_ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
