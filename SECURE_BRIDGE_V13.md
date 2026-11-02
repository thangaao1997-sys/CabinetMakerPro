# AI IDEA V1.3 — Signed file-drop protocol (offline preview only)

This is **protocol preparation**, not a functioning iPhone-to-Windows connection.

## What is implemented

- HMAC-SHA256 signed Vietnamese command envelopes.
- 16-byte random nonces and a short lifetime (five minutes, up to one minute future clock skew).
- Persistent SQLite replay ledger (unique nonces).
- Read-only command planning after signature verification.
- Locked-design model writes remain blocked.
- No listening network port, RPC endpoint, file watcher, SketchUp write or CNC output.

## Local reference usage

For **development only**, generate a random 32-byte key and store it securely on the local machine. Do not paste keys into ChatGPT, GitHub, or support messages. The sample key in unit tests is not secret and **must never be used in deployment**.

A trusted sender can call:

```python
from core.secure_requests import sign_payload
envelope = sign_payload({
  "request_id": "DEMO-001",
  "text": "Tạo tủ bếp rộng 600 mm sâu 560 mm cao 820 mm",
  "target_model_locked": False
}, secret_bytes)
```

A Windows-side verifier (once deliberately configured with the same secret) can run:

```bash
python -m core.secure_preview --input signed-command.json --ledger ./local/nonce-ledger.sqlite
```

The verifier reads `AI_IDEA_SHARED_KEY_HEX` from its **local** environment and will refuse to run when it is missing. This is for development/test usage; production needs robust secret storage, host authentication, access-control review, approved command routing and real Windows/SketchUp integration tests.

## Security limits

A valid signature establishes that the signer knew a shared secret. It does **not** prove user identity, authorize a model modification, approve workshop standards or permit CNC. The in-memory ChatGPT conversation is **not** itself an authorized signing endpoint.

SQLite replay protection is local-host only; deployment must control directory permissions, key rotation, backup and clock synchronization. An offline prototype is not an audited production security solution.
