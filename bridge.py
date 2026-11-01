"""Local file-drop bridge, NOT a network server. Python stdlib only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
from core.pipeline import generate

MAX_BYTES = 128000

def process_one(source: Path, output: Path) -> dict:
    source = Path(source)
    if not source.is_file() or source.is_symlink() or source.suffix.lower() != ".json":
        raise ValueError("Only a regular local JSON file is accepted")
    if source.stat().st_size > MAX_BYTES:
        raise ValueError("Command exceeds 128 KB")
    raw = source.read_bytes()
    command = json.loads(raw.decode("utf-8"))
    result = generate(command)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    name = hashlib.sha256(raw).hexdigest()[:16]
    destination = output / ("ai_idea_draft_" + name + ".json")
    if destination.exists():
        raise FileExistsError("Output already exists: refusing overwrite")
    payload = json.dumps(result["scene"], ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    tmp = output / (destination.name + ".tmp")
    if tmp.exists():
        raise FileExistsError("Temporary output exists")
    try:
        with tmp.open("x", encoding="utf-8") as f:
            f.write(payload)
        os.replace(tmp, destination)
    finally:
        tmp.unlink(missing_ok=True)
    return {"source": str(source), "scene": str(destination),
            "request_id": result["scene"]["request_id"],
            "manufacturing_approved": False,
            "objects": len(result["scene"]["objects"])}

def main():
    parser = argparse.ArgumentParser(description="AI IDEA local offline draft importer")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(json.dumps(process_one(Path(args.input), Path(args.output)), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
