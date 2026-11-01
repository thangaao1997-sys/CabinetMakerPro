"""V0.7 geometry audit: drafts only, dimensions in millimetres."""
from collections import defaultdict
from math import isfinite

class AuditError(ValueError):
    pass

AXES=("x","y","z")

def number(x, positive=False):
    if type(x) not in (int,float) or not isfinite(x) or (positive and x<=0):
        raise AuditError("Invalid numeric dimension")
    return x

def audit_draft(draft):
    if not isinstance(draft,dict) or draft.get("schema_version")!="ai-idea.parts.v1" or draft.get("manufacturing_approved") is not False:
        raise AuditError("Only unapproved parts draft accepted")
    env=draft.get("envelope_mm",{})
    if set(env)!={"width","depth","height"}: raise AuditError("Invalid envelope")
    limits=[number(env[k],True) for k in ("width","depth","height")]
    parts=draft.get("parts")
    if not isinstance(parts,list) or not 1<=len(parts)<=2000: raise AuditError("Invalid parts")
    bounds=[];codes=set();overlaps=[]
    for p in parts:
        if not isinstance(p,dict) or not isinstance(p.get("code"),str) or not p["code"] or p["code"] in codes: raise AuditError("Invalid or duplicate code")
        codes.add(p["code"])
        if p.get("quantity") != 1 or type(p.get("quantity")) is not int: raise AuditError("One placed part required")
        o=p.get("origin_mm",{});s=p.get("size_mm",{})
        if set(o)!=set(AXES) or set(s)!=set(AXES): raise AuditError("Incomplete box")
        start=[number(o[k]) for k in AXES];size=[number(s[k],True) for k in AXES]
        if any(start[i]<0 or start[i]+size[i]>limits[i]+1e-7 for i in range(3)): raise AuditError("Box outside envelope")
        for code,lo,sz in bounds:
            if all(min(start[i]+size[i],lo[i]+sz[i])-max(start[i],lo[i])>1e-7 for i in range(3)):
                overlaps.append([code,p["code"]])
        bounds.append((p["code"],start,size))
    return {"valid_geometry":not overlaps,"part_count":len(parts),"overlaps":overlaps,"manufacturing_approved":False}

def export_scene(draft):
    check=audit_draft(draft)
    if not check["valid_geometry"]: raise AuditError("Colliding parts")
    objects=[]
    for p in draft["parts"]:
        if p.get("material") not in ("panel","back"): raise AuditError("Unknown material")
        objects.append({"id":p["code"],"role":p.get("role","unspecified"),"material":p["material"],
            "origin_mm":dict(p["origin_mm"]),"size_mm":dict(p["size_mm"])})
    return {"schema_version":"ai-idea.scene.v1","units":"mm","request_id":draft["request_id"],
        "envelope_mm":dict(draft["envelope_mm"]),"manufacturing_approved":False,"objects":objects,"audit":check}

def cutting_preview(draft):
    check=audit_draft(draft)
    if not check["valid_geometry"]: raise AuditError("Colliding parts")
    rows=defaultdict(int)
    axes={"left_side":"x","right_side":"x","top":"z","bottom":"z","overlay_back":"y"}
    for p in draft["parts"]:
        ax=axes.get(p.get("role"))
        if ax is None or p.get("material") not in ("panel","back"): raise AuditError("Unknown role/material")
        s=p["size_mm"]
        a,b=[s[k] for k in AXES if k!=ax]
        rows[(p["material"],s[ax],a,b)]+=1
    return {"production_ready":False,"units":"mm","rows":[{"material":k[0],"thickness_mm":k[1],
        "a_mm":k[2],"b_mm":k[3],"quantity":n,"edge_banding":"unconfirmed","grain":"unconfirmed"} for k,n in sorted(rows.items())],
        "warnings":["Prototype layout is not approved for manufacturing"]}
