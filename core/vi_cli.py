"""Vietnamese sentence -> validated non-production scene JSON, offline only."""
import argparse
import json
from pathlib import Path
from .vi_intent import parse_vietnamese
from .pipeline import generate

def preview_sentence(sentence, request_id="IDEA-DRAFT"):
    command = parse_vietnamese(sentence, request_id)
    result = generate(command)
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
