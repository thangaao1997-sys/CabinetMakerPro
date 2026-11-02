"""Build a deterministic, read-only AI IDEA Windows starter ZIP.

Includes only reviewed Python sources, a manual preflight .cmd and an RBZ
verified against checked-in Ruby source. Does not include secrets or installers.
"""
import argparse
import hashlib
from pathlib import Path
import zipfile

from .windows_preflight import inspect_rbz, PreflightError

ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    "bridge.py",
    "core/__init__.py",
    "core/ai_idea_core.py",
    "core/audit.py",
    "core/command_center.py",
    "core/parts.py",
    "core/pipeline.py",
    "core/secure_preview.py",
    "core/secure_requests.py",
    "core/vi_cli.py",
    "core/vi_intent.py",
    "tools/__init__.py",
    "tools/windows_preflight.py",
    "examples/kitchen_command.json",
    "examples/scene.json",
    "WINDOWS_V14.md",
    "V15_DIAGNOSTICS.md",
    "V16_V17_MODEL_SAFETY.md",
    "V18_INTEGRITY.md",
    "windows/AI_IDEA_CHECK.cmd",
)
DESTINATIONS = {
    "windows/AI_IDEA_CHECK.cmd": "AI_IDEA_CHECK.cmd",
    "V18_INTEGRITY.md": "README_WINDOWS.md",
}
STAMP = (2026, 1, 1, 0, 0, 0)


def build_bundle(output, rbz, root=ROOT):
    root = Path(root).resolve()
    output = Path(output).resolve()
    rbz = Path(rbz).resolve()
    inspect_rbz(rbz, source_root=root)
    if output.exists():
        raise FileExistsError("Refusing to overwrite Windows starter archive")
    entries = []
    for rel in SOURCES:
        source = root / rel
        if source.is_symlink() or not source.is_file():
            raise ValueError("Missing or linked bundle source: " + rel)
        target = DESTINATIONS.get(rel, rel)
        entries.append((target, source.read_bytes()))
    entries.append(("AI_IDEA_V18_ALPHA.rbz", rbz.read_bytes()))
    names = [name for name, _ in entries]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate starter archive member")
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, content in sorted(entries):
                info = zipfile.ZipInfo(name, date_time=STAMP)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                archive.writestr(info, content, compress_type=zipfile.ZIP_DEFLATED)
        with zipfile.ZipFile(output) as archive:
            if archive.testzip() is not None or sorted(archive.namelist()) != sorted(names):
                raise ValueError("Windows starter validation failed")
        return {
            "path": str(output),
            "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "files": len(entries),
            "read_only": True,
        }
    except Exception:
        output.unlink(missing_ok=True)
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rbz", required=True)
    parser.add_argument("--output", default="dist/AI_IDEA_V18_WINDOWS_STARTER.zip")
    args = parser.parse_args()
    print(build_bundle(args.output, args.rbz))


if __name__ == "__main__":
    main()
