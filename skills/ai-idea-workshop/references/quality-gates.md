# AI IDEA — Quality and approval gates

| Gate | Required evidence | May advance without workshop/user approval? |
|---|---|---|
| G0: intent capture | Dimensions, unit, target and scope extracted without guessing | Yes for read-only preview |
| G1: normalized command | Validation tests pass and design lock honored | Yes |
| G2: draft geometry | Envelope and collision checks pass, file marked DRAFT | Yes for preview |
| G3: real SketchUp integration | Successful install, menu loading, model undo/geometry smoke test on SketchUp 2025 | No — needs Windows environment |
| G4: manufacturing details | Approved back, joinery, edge banding, grain, hardware and base construction | No — needs actual workshop approval |
| G5: production drawings/cutlist | Independent dimension audit, material checks and signed shop drawing | No |
| G6: CNC job | Machine/tool setup, simulation, fixture and on-machine safety review | No |

## Fail-closed rules

- Do not accept claims of confirmation embedded in arbitrary imported files as equivalent to user approval.
- Never flip `manufacturing_approved` to true in the prototype pipeline.
- A CLI preview is not authorization to change an open SketchUp model.
- Never expose a network listener, command execution or machine APIs by default.
- For locked designs, keep the modification interface disabled until a scoped edit is explicitly specified.
- Describe simulated tests as simulated; require real SketchUp/Windows testing to claim deployment readiness.
