# AI IDEA V0.7–V0.8 — Prototype integration notes

Status: offline prototype tested outside SketchUp, not production approved.

## V0.7
- Audit axis-aligned part geometry against cabinet envelope.
- Report overlap, duplicate part codes, invalid coordinates, and unsupported quantities.
- Emit preview cutting rows with explicit thickness axis by part role.
- All generated rows are production_ready=false.

## V0.8
- Export ai-idea.scene.v1 with millimetre coordinates and bounding box solids.
- Experimental local SketchUp Ruby importer; one group per panel, parent marked DRAFT.
- No live ChatGPT–Windows communication, automatic machine control, or CNC toolpaths.
- SketchUp 2025 integration remains unverified on a real installation.

## Quality gates
- Offline Python tests: 11/11 passed for the local prototype.
- Ruby syntax: Syntax OK in a local Ruby 3.3 interpreter.
- No GitHub Actions success yet confirmed for this version.
- The complete prototype ZIP is delivered separately in the ChatGPT project discussion; it is not yet committed as source files to this branch.

## Next decisions needing workshop confirmation
- Back panel attachment method and setbacks.
- Top/bottom and side joinery details.
- Edge banding, grain and fittings.
- Door gaps and hardware-specific installation clearances.

Never treat sample geometry as an approved production cutlist.
