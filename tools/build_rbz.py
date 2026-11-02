"""Build a reproducible SketchUp RBZ from the repository source.

Usage: python -m tools.build_rbz --output dist/AI_IDEA_V18_ALPHA.rbz
No external dependencies, no network or SketchUp access.
"""
import argparse
import hashlib
import os
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "plugin/ai_idea_v10.rb",
    "plugin/ai_idea_v10/main.rb",
    "plugin/ai_idea_v10/scene_importer.rb",
    "plugin/ai_idea_v10/diagnostics.rb",
    "plugin/ai_idea_v10/model_audit.rb",
)

def build(output, root=ROOT):
    root = Path(root).resolve()
    output = Path(output).resolve()
    entries = []
    for rel in FILES:
        source = root / rel
        if source.is_symlink() or not source.is_file():
            raise ValueError("Required extension source is missing or linked: " + rel)
        content = source.read_bytes()
        if not content:
            raise ValueError("Empty extension file: " + rel)
        # Strip "plugin/" so the loader is at the RBZ archive root.
        entries.append((rel[len("plugin/"):], content))
    if output.exists():
        raise FileExistsError("Refusing to overwrite existing RBZ")
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name, content in entries:
                info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                archive.writestr(info, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        with zipfile.ZipFile(output) as archive:
            if archive.testzip() is not None or sorted(archive.namelist()) != sorted(name for name, _ in entries):
                raise ValueError("Invalid RBZ archive content")
        return {"path": str(output), "sha256": hashlib.sha256(output.read_bytes()).hexdigest(), "files": len(entries)}
    except Exception:
        output.unlink(missing_ok=True)
        raise

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="dist/AI_IDEA_V1_ALPHA.rbz")
    args = parser.parse_args()
    print(build(args.output))

if __name__ == "__main__":
    main()
