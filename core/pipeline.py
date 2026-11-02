"""AI IDEA V0.9 local draft pipeline."""
import argparse
import json
from pathlib import Path
from .ai_idea_core import CommandError
from .parts import draft_parts
from .audit import audit_draft, export_scene, cutting_preview, AuditError

def generate(command):
    draft=draft_parts(command)
    report=audit_draft(draft)
    if not report["valid_geometry"]: raise AuditError("Collision detected")
    return {"parts":draft,"audit":report,"scene":export_scene(draft),"cutting_preview":cutting_preview(draft)}

def write_bundle(input_path, output_dir):
    src=Path(input_path)
    if src.stat().st_size>128000: raise CommandError("Input too large")
    command=json.loads(src.read_text(encoding="utf-8"))
    bundle=generate(command)
    target=Path(output_dir)
    target.mkdir(parents=True,exist_ok=True)
    for name,data in bundle.items():
        (target/(name+".json")).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    return target

def main():
    p=argparse.ArgumentParser()
    p.add_argument("input_json");p.add_argument("output_directory")
    a=p.parse_args();print("DRAFT ONLY:",write_bundle(a.input_json,a.output_directory))
if __name__=="__main__": main()
