"""AI IDEA command validation, stdlib only. All dimensions are mm."""
import json
from pathlib import Path

SCHEMA = "ai-idea.command.v1"
TYPES = {"kitchen", "wardrobe", "shoe", "other"}
FIELDS = {"schema_version", "request_id", "cabinet_type", "dimensions_mm", "materials_mm", "base_mm", "design_lock"}

class CommandError(ValueError):
    pass

def positive(name, x, allow_zero=False):
    if type(x) not in (int, float) or not (float("-inf") < x < float("inf")):
        raise CommandError(f"{name} must be a finite number")
    if x < 0 or (x == 0 and not allow_zero):
        raise CommandError(f"{name} must be positive" if not allow_zero else f"{name} must be non-negative")
    return x

def validate_command(p):
    if not isinstance(p, dict) or set(p) - FIELDS:
        raise CommandError("invalid command object or unknown fields")
    if p.get("schema_version") != SCHEMA:
        raise CommandError("unsupported schema_version")
    rid = p.get("request_id")
    if not isinstance(rid, str) or not rid.strip() or len(rid) > 100:
        raise CommandError("invalid request_id")
    kind = p.get("cabinet_type")
    if kind not in TYPES:
        raise CommandError("invalid cabinet_type")
    d = p.get("dimensions_mm")
    if not isinstance(d, dict) or set(d) != {"width", "depth", "height"}:
        raise CommandError("dimensions_mm requires width, depth, height")
    dimensions = {k:positive(k,d[k]) for k in ("width","depth","height")}
    m = p.get("materials_mm", {"panel":17,"back":7})
    if not isinstance(m,dict) or set(m) != {"panel","back"}:
        raise CommandError("materials_mm requires panel and back")
    materials = {k:positive(k,m[k]) for k in ("panel","back")}
    if 2*materials["panel"] >= dimensions["width"] or 2*materials["panel"] >= dimensions["height"]:
        raise CommandError("panel thickness incompatible with exterior size")
    if materials["back"] >= dimensions["depth"]:
        raise CommandError("back panel thicker than available depth")
    base = p.get("base_mm")
    if kind == "kitchen":
        base = 100 if base is None else positive("base_mm",base,True)
        if base != 100:
            raise CommandError("kitchen base is 100 mm; exceptions need separately approved policy")
    else:
        if base is None:
            raise CommandError("non-kitchen base_mm must be explicit")
        base = positive("base_mm",base,True)
        if base not in (0,17,50):
            raise CommandError("non-kitchen base must be an explicitly approved 0, 17, or 50 mm")
    if base >= dimensions["height"]:
        raise CommandError("base height must be below overall height")
    lock = p.get("design_lock",False)
    if type(lock) is not bool:
        raise CommandError("design_lock must be boolean")
    return {"schema_version":SCHEMA,"request_id":rid.strip(),"cabinet_type":kind,
            "dimensions_mm":dimensions,"materials_mm":materials,"base_mm":base,
            "design_lock":lock,"body_height_mm":dimensions["height"]-base,
            "manufacturing_approved":False}

def load_command(path):
    path = Path(path)
    if path.stat().st_size > 128000:
        raise CommandError("JSON file too large")
    return validate_command(json.loads(path.read_text(encoding="utf-8")))
