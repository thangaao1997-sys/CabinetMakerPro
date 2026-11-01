"""Offline signed-request format for a future AI IDEA Windows connector.

This module authenticates intent envelopes but does NOT authorize SketchUp
modification, start a network listener, or execute machine commands.
Python standard library only.
"""
import hashlib
import hmac
import json
import re
import secrets
import sqlite3
import time
from pathlib import Path

VERSION = "ai-idea.signed-request.v1"
MAX_TEXT = 500
MAX_AGE_SECONDS = 300
MAX_FUTURE_SECONDS = 60
_HEX_32 = re.compile(r"^[0-9a-f]{32}$")
_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
_PAYLOAD_KEYS = {"request_id", "text", "target_model_locked"}
_BODY_KEYS = {"schema_version", "issued_at", "nonce", "payload"}


class EnvelopeError(ValueError):
    pass


def _secret_check(secret):
    if not isinstance(secret, bytes) or len(secret) < 32:
        raise EnvelopeError("The HMAC secret must be >=32 random bytes")


def _validate_payload(payload):
    if not isinstance(payload, dict) or set(payload) != _PAYLOAD_KEYS:
        raise EnvelopeError("Invalid payload shape")
    rid = payload["request_id"]
    sentence = payload["text"]
    locked = payload["target_model_locked"]
    if not isinstance(rid, str) or not 0 < len(rid.strip()) <= 100:
        raise EnvelopeError("Invalid request ID")
    if not isinstance(sentence, str) or not 0 < len(sentence) <= MAX_TEXT:
        raise EnvelopeError("Invalid Vietnamese command")
    if type(locked) is not bool:
        raise EnvelopeError("target_model_locked must be boolean")
    return payload


def _encoded(body):
    return json.dumps(
        body, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def sign_payload(payload, secret, *, issued_at=None, nonce=None):
    """Create a signed short-lived envelope. Do not share secrets in chat."""
    _secret_check(secret)
    _validate_payload(payload)
    issued_at = int(time.time()) if issued_at is None else issued_at
    nonce = secrets.token_hex(16) if nonce is None else nonce
    if type(issued_at) is not int or issued_at < 0:
        raise EnvelopeError("issued_at must be a nonnegative integer")
    if not isinstance(nonce, str) or not _HEX_32.fullmatch(nonce):
        raise EnvelopeError("nonce must be 16 bytes in lowercase hex")
    body = {
        "schema_version": VERSION, "issued_at": issued_at,
        "nonce": nonce, "payload": payload,
    }
    digest = hmac.new(secret, _encoded(body), hashlib.sha256).hexdigest()
    return {**body, "signature": digest}


class SQLiteNonceLedger:
    """Atomic replay detection for a local, single-host SQLite database."""

    def __init__(self, path):
        self.path = Path(path)

    def claim(self, nonce, expiry, now):
        if self.path.is_symlink():
            raise EnvelopeError("Replay-ledger symlinks are not accepted")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with sqlite3.connect(str(self.path), timeout=10) as con:
                con.execute("BEGIN IMMEDIATE")
                con.execute(
                    "CREATE TABLE IF NOT EXISTS used_nonces ("
                    "nonce TEXT PRIMARY KEY, expires_at INTEGER NOT NULL)"
                )
                con.execute("DELETE FROM used_nonces WHERE expires_at < ?", (now,))
                try:
                    con.execute(
                        "INSERT INTO used_nonces (nonce, expires_at) VALUES (?, ?)",
                        (nonce, expiry)
                    )
                except sqlite3.IntegrityError:
                    return False
        except sqlite3.Error as exc:
            raise EnvelopeError("Unable to check replay ledger") from exc
        return True


def verify_envelope(envelope, secret, ledger, *, now=None):
    """Verify signature + expiry + persistent replay check; return payload.

    Authentication is separate from authorization: callers MUST evaluate the
    design lock, workshop approval and model write permissions afterwards.
    """
    _secret_check(secret)
    if not isinstance(envelope, dict) or set(envelope) != _BODY_KEYS | {"signature"}:
        raise EnvelopeError("Unexpected envelope fields")
    sig = envelope["signature"]
    if not isinstance(sig, str) or not _HEX_64.fullmatch(sig):
        raise EnvelopeError("Invalid signature format")
    body = {key: envelope[key] for key in _BODY_KEYS}
    if body["schema_version"] != VERSION:
        raise EnvelopeError("Unsupported envelope version")
    timestamp = body["issued_at"]
    nonce = body["nonce"]
    if type(timestamp) is not int or timestamp < 0:
        raise EnvelopeError("Invalid issued_at")
    if not isinstance(nonce, str) or not _HEX_32.fullmatch(nonce):
        raise EnvelopeError("Invalid nonce")
    _validate_payload(body["payload"])
    expected = hmac.new(secret, _encoded(body), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        raise EnvelopeError("Invalid HMAC signature")
    now = int(time.time()) if now is None else now
    if type(now) is not int or now < 0:
        raise EnvelopeError("Invalid verification clock")
    if timestamp < now - MAX_AGE_SECONDS or timestamp > now + MAX_FUTURE_SECONDS:
        raise EnvelopeError("Request expired or clock too far ahead")
    if not isinstance(ledger, SQLiteNonceLedger):
        raise EnvelopeError("Persistent replay ledger required")
    if not ledger.claim(nonce, timestamp + MAX_AGE_SECONDS, now):
        raise EnvelopeError("Replay of an already processed request")
    return body["payload"]
