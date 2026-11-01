"""Vietnamese sentence -> validated non-production scene JSON, offline only."""
import argparse
import json
from pathlib import Path
from .vi_intent import parse_vietnamese
from .pipeline import generate

def preview_sentence(sentence, request_id="IDEA-DRAFT"):
    command = parse_vietnamese(sentence, request_id)
    # The intent parser returns a validated, enriched command.\n    # The pipeline accepts only its strict input schema, so remove derived fields.\n    raw_command = {key: command[key] for key in (\n        'schema_version', 'request_id', 'cabinet_type', 'dimensions_mm',\n        'materials_mm', 'base_mm', 'design_lock'\n    )}\n    result = generate(raw_command)
    return {"command": command, "scene": result["scene"],
            "audit": result["audit"], "cutting_preview": result["cutting_preview"],
            "manufacturing_approved": False}

def main():
    parser = argparse.ArgumentParser(description="AI IDEA Vietnamese draft command")
    parser.add_argument("--text", required=True)
    parser.add_argument("--request-id", default="IDEA-DRAFT")
    args = parser.parse_args()
    print(json.dumps(preview_sentence(args.text,args.request_id),
                     ensure_ascii=False, indent=2, allow_nan=False))

if __name__=="__main__":
    main()
