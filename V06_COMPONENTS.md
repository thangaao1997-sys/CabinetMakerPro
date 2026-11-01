# AI IDEA V0.6: draft components

This prototype is NOT an approved IDEA shop-drawing or CNC standard.

- Input: validated ai-idea.command.v1 JSON (mm)
- Output: ai-idea.parts.v1, 5 conceptual panels + draft cut rows
- Assumed construction: full-height sides; top and bottom between sides
- Assumed back: overlay rear at 7 mm, nominal carcass depth excludes back
- Abstract base: height is accounted for, **base itself is not generated**
- No doors, hardware, edge banding, grain direction or joinery are specified
- All parts report manufacturing_approved=false; cutlist rows production_ready=false

## Run
```sh
python -m unittest discover -s tests -v
```

## Example
```python
from core.parts import draft_parts, draft_cut_list
cmd={"schema_version":"ai-idea.command.v1","request_id":"demo",
     "cabinet_type":"kitchen","dimensions_mm":{"width":600,"depth":560,"height":820}}
data=draft_parts(cmd)
print(draft_cut_list(data))
```

Do not export CNC or approve production using this prototype.
