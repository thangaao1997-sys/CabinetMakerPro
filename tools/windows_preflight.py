"""AI IDEA V1.4: read-only Windows + SketchUp extension preflight.

This script does NOT install, open or control SketchUp. It never starts
a network service, modifies a model, or approves CNC output.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import zipfile

EXPECTED = {
    "ai_idea_v10.rb": "plugin/ai_idea_v10.rb",
    "ai_idea_v10/main.rb": "plugin/ai_idea_v10/main.rb",
    "ai_idea_v10/scene_importer.rb": "plugin/ai_idea_v10/scene_importer.rb",
    "ai_idea_v10/diagnostics.rb": "plugin/ai_idea_v10/diagnostics.rb",
    "ai_idea_v10/model_audit.rb": "plugin/ai_idea_v10/model_audit.rb",
    "ai_idea_v10/geometry_fingerprint.rb": "plugin/ai_idea_v10/geometry_fingerprint.rb",
}
MAX_COMPRESSED_BYTES = 2_000_000
MAX_EXTRACTED_BYTES = 2_000_000


class PreflightError(ValueError):
    pass


def inspect_rbz(archive_path, source_root=None):
    """Verify extension layout, CRC, sizes and optionally exact source parity."""
    archive_path = Path(archive_path)
    if archive_path.is_symlink() or not archive_path.is_file():
        raise PreflightError("RBZ must be a regular file, not a symlink")
    if archive_path.stat().st_size > MAX_COMPRESSED_BYTES:
        raise PreflightError("RBZ archive exceeds safe inspection limit")
    try:
        with zipfile.ZipFile(archive_path) as archive:
            members = archive.infolist()
            names = [item.filename for item in members]
            if len(members) != len(EXPECTED) or set(names) != set(EXPECTED):
                raise PreflightError("RBZ must contain exactly the expected loader and five Ruby files")
            if len(names) != len(set(names)):
                raise PreflightError("RBZ contains duplicate names")
            if any(item.is_dir() or item.flag_bits & 1 for item in members):
                raise PreflightError("Directories or encrypted members are not permitted")
            if sum(item.file_size for item in members) > MAX_EXTRACTED_BYTES:
                raise PreflightError("RBZ uncompressed size exceeds safe inspection limit")
            contents = {item.filename: archive.read(item) for item in members}
            if archive.testzip() is not None:
                raise PreflightError("RBZ CRC integrity check failed")
    except (zipfile.BadZipFile, zipfile.LargeZipFile, RuntimeError, OSError) as exc:
        raise PreflightError("Unreadable or corrupted RBZ") from exc

    if b"SketchupExtension.new" not in contents["ai_idea_v10.rb"]:
        raise PreflightError("Extension loader definition not found")
    if b"SceneImporter" not in contents["ai_idea_v10/scene_importer.rb"]:
        raise PreflightError("Missing scene import module")
    if source_root is not None:
        root = Path(source_root).resolve()
        for member, rel in EXPECTED.items():
            source = root / rel
            if source.is_symlink() or not source.is_file():
                raise PreflightError("Missing source for verification: " + rel)
            if contents[member] != source.read_bytes():
                raise PreflightError("Archive differs from repository source: " + rel)
    return {
        "valid": True,
        "sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
        "files": sorted(names),
        "source_parity_checked": source_root is not None,
    }


def inspect_host(*, os_name=None, appdata=None, program_files=None, python_version=None):
    """Host detection only; existence is not a successful SketchUp smoke test."""
    os_name = platform.system() if os_name is None else os_name
    appdata = os.environ.get("APPDATA", "") if appdata is None else appdata
    program_files = os.environ.get("ProgramFiles", "") if program_files is None else program_files
    python_version = sys.version_info[:2] if python_version is None else python_version
    windows = os_name == "Windows"
    executable = (Path(program_files) / "SketchUp" / "SketchUp 2025" / "SketchUp.exe") if (windows and program_files) else None
    plugin_dir = (Path(appdata) / "SketchUp" / "SketchUp 2025" / "SketchUp" / "Plugins") if (windows and appdata) else None
    return {
        "os": os_name,
        "windows": windows,
        "python_compatible": tuple(python_version) >= (3, 11),
        "sketchup_exe_detected": bool(executable and executable.is_file()),
        "sketchup_plugin_directory_detected": bool(plugin_dir and plugin_dir.is_dir()),
        "sketchup_exe_candidate": str(executable) if executable else None,
        "plugins_dir_candidate": str(plugin_dir) if plugin_dir else None,
        "actual_sketchup_execution_tested": False,
    }


def make_report(rbz, source_root=None, **host_overrides):
    archive = inspect_rbz(rbz, source_root=source_root)
    host = inspect_host(**host_overrides)
    return {
        "schema_version": "ai-idea.windows-preflight.v1",
        "status": "ready_for_manual_smoke_test" if (
            host["windows"] and host["python_compatible"] and host["sketchup_exe_detected"]
        ) else "host_needs_attention",
        "rbz": archive,
        "host": host,
        "design_changes_performed": False,
        "software_installed": False,
        "network_access_started": False,
        "manufacturing_approved": False,
        "next_action": "Install the RBZ via SketchUp Extension Manager and verify menu/Undo manually.",
    }


def main():
    parser = argparse.ArgumentParser(description="Read-only AI IDEA Windows readiness check")
    parser.add_argument("--rbz", required=True)
    parser.add_argument("--source-root", default=None)
    args = parser.parse_args()
    try:
        report = make_report(args.rbz, source_root=args.source_root)
    except PreflightError as exc:
        parser.error(str(exc))
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["rbz"]["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
