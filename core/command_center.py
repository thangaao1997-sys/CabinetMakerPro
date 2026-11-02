"""AI IDEA Command Center V1.2: deterministic, read-only work planning.

Converts a narrowly supported Vietnamese cabinet creation command into a
validated draft scene preview. This module cannot write SketchUp or CNC files.
"""
import argparse
import hashlib
import json

from .ai_idea_core import CommandError
from .audit import AuditError
from .pipeline import generate
from .vi_intent import IntentError, parse_vietnamese

SCHEMA = "ai-idea.workplan.v1"
INPUT_FIELDS = ("schema_version", "request_id", "cabinet_type",
                "dimensions_mm", "materials_mm", "base_mm", "design_lock")


def plan_request(text, request_id="IDEA-DRAFT", target_model_locked=False):
    """Return an immutable-intent preview or a refusal. No external actions.

    A locked target is never modified (nor interpreted as permission to create
    elements in the locked model). The code has no approval or execution API.
    """
    if type(target_model_locked) is not bool:
        raise TypeError("target_model_locked must be a boolean")
    if type(request_id) is not str or not request_id.strip() or len(request_id) > 100:
        raise ValueError("request_id must be a non-empty string of <=100 chars")

    base = {
        "schema_version": SCHEMA,
        "request_id": request_id,
        "mode": "preview_only",
        "side_effects": [],
        "manufacturing_approved": False,
        "model_write_allowed": False,
        "cnc_export_allowed": False,
        "requires_model_review": True,
        "requires_workshop_approval": True,
    }

    if target_model_locked:
        return {
            **base,
            "status": "blocked_locked_design",
            "reason": "Existing model is locked; cannot infer permission to alter it.",
            "preview": None,
        }

    try:
        normalized = parse_vietnamese(text, request_id)
        # Strict parser returns derived fields, but downstream validator
        # deliberately accepts only the original command schema.
        raw = {key: normalized[key] for key in INPUT_FIELDS}
        output = generate(raw)
    except (IntentError, CommandError, AuditError, TypeError, ValueError) as exc:
        return {
            **base,
            "status": "rejected",
            "reason": str(exc),
            "preview": None,
        }

    command_digest = hashlib.sha256(
        json.dumps(raw, ensure_ascii=False, sort_keys=True,
                   separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    preview = {
        "command": normalized,
        "scene": output["scene"],
        "audit": output["audit"],
        "cutting_preview": output["cutting_preview"],
        "missing_decisions": output["parts"]["missing_decisions"],
    }
    return {
        **base,
        "status": "draft_preview_ready",
        "command_sha256": command_digest,
        "preview": preview,
    }


def main():
    parser = argparse.ArgumentParser(
        description="AI IDEA safe Vietnamese command preview (no machine control)"
    )
    parser.add_argument("--text", required=True)
    parser.add_argument("--request-id", default="IDEA-DRAFT")
    parser.add_argument("--target-model-locked", action="store_true")
    arguments = parser.parse_args()
    result = plan_request(
        arguments.text,
        request_id=arguments.request_id,
        target_model_locked=arguments.target_model_locked,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    # Rejected or locked requests should fail in CI/CLI integrations.
    return 0 if result["status"] == "draft_preview_ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
