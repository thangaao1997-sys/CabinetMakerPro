# AI IDEA V1.0-alpha — Offline bridge build

Build date: 2026-11-01.

## Delivered artifacts
- `AI_IDEA_V1_0_ALPHA.rbz`: SketchUp extension with an Extensions-menu JSON scene picker (available as an attachment in the AI IDEA chat)
- `AI_IDEA_V1_0_ALPHA_SOURCE.zip`: full source including `bridge.py`, tests and example requests (available in the chat)
- Source artifacts are not yet fully imported into this GitHub branch; this is a status marker only.

## Verified outside SketchUp
- 28/28 Python tests passed (includes previous V0.9 suite and new file-drop bridge tests)
- 6/6 Ruby parser checks passed
- 4/4 Ruby mocked SketchUp import checks passed
- Ruby syntax checks passed for all RBZ scripts
- ZIP archive integrity checked

## What the package does
Manual Windows file workflow: validated command JSON -> Python CLI bridge -> draft scene JSON -> explicit selection in SketchUp extension -> draft box groups.

No HTTP service, no public network listener, no remote phone control.
No production approval, CNC export or automatic machining.
Construction and base geometry remain unapproved prototype assumptions.

## Real-world gate
Before considering the plugin validated, test the RBZ in SketchUp 2025 on Windows. Do not assume mock API behavior guarantees production application compatibility.

## Next
- Import source files into this development branch after parity verification.
- Add diagnostics and signed command provenance if future network services are authorized.
- Obtain workshop decisions for joinery, setbacks, hinge/slide hardware and edge banding before production output.
