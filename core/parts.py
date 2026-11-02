"""AI IDEA V0.6: NONPRODUCTION prototype carcass component generator (mm)."""
from collections import defaultdict
from .ai_idea_core import validate_command, CommandError

LAYOUT = "between_sides_overlay_back_v0"

def draft_parts(command, layout=LAYOUT):
    """X width; Y front-to-back; Z height. Side full height; top/bottom between sides.
    Back overlays rear, consuming nominal overall depth. Base is NOT modelled.
    This is explicitly NOT an approved IDEA workshop construction.
    """
    if layout != LAYOUT:
        raise CommandError("Unsupported prototype construction")
    c = validate_command(command)
    w,d,h = (c["dimensions_mm"][k] for k in ("width","depth","height"))
    t,b = c["materials_mm"]["panel"], c["materials_mm"]["back"]
    bh,z = c["body_height_mm"],c["base_mm"]
    inner_w, carcass_d = w-2*t,d-b
    if bh <= 2*t or carcass_d <= 0 or inner_w <= 0:
        raise CommandError("Insufficient space for prototype carcass")
    def part(code,role,size,origin,material):
        if any(v <= 0 for v in size): raise CommandError("Nonpositive panel size")
        return {"code":code,"role":role,"material":material,
                "size_mm":dict(zip(("x","y","z"),size)),
                "origin_mm":dict(zip(("x","y","z"),origin)),
                "quantity":1,"edgebanding":"unconfirmed","grain_direction":"unconfirmed"}
    parts = [
        part("SIDE-L","left_side",(t,carcass_d,bh),(0,0,z),"panel"),
        part("SIDE-R","right_side",(t,carcass_d,bh),(w-t,0,z),"panel"),
        part("TOP","top",(inner_w,carcass_d,t),(t,0,z+bh-t),"panel"),
        part("BOTTOM","bottom",(inner_w,carcass_d,t),(t,0,z),"panel"),
        part("BACK","overlay_back",(w,b,bh),(0,carcass_d,z),"back")]
    for p in parts:
        for ax,limit in (("x",w),("y",d),("z",h)):
            if p["origin_mm"][ax]<0 or p["origin_mm"][ax]+p["size_mm"][ax]>limit:
                raise CommandError("Panel exceeds envelope")
    return {"schema_version":"ai-idea.parts.v1","request_id":c["request_id"],
            "construction":layout,"construction_status":"prototype_unapproved",
            "manufacturing_approved":False,"units":"mm","envelope_mm":c["dimensions_mm"],
            "base_mm":z,"base_structure":"not_generated","parts":parts,
            "missing_decisions":["base_structure","door_configuration","joinery",
                "edgebanding","grain_direction","hardware","installation_clearances"],
            "warnings":["Not an approved IDEA workshop construction",
                "Back overlays rear, consuming depth","No CNC or production cutlist"]}

def draft_cut_list(draft):
    if draft.get("schema_version") != "ai-idea.parts.v1" or draft.get("manufacturing_approved") is not False:
        raise CommandError("Expected nonproduction parts draft")
    rows=defaultdict(int)
    for p in draft["parts"]:
        s=p["size_mm"]
        axis="y" if p["role"]=="overlay_back" else ("x" if p["role"] in ("left_side","right_side") else "z")
        a,b=(s[k] for k in ("x","y","z") if k!=axis)
        rows[(p["material"],s[axis],a,b)]+=p["quantity"]
    return [{"material":k[0],"thickness_mm":k[1],"cut_a_mm":k[2],
             "cut_b_mm":k[3],"quantity":n,"production_ready":False}
            for k,n in sorted(rows.items())]
