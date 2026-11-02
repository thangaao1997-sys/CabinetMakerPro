---
name: ai-idea-workshop
description: "Use when helping with IDEA workshop cabinetry, SketchUp 2025 Ruby plugins, panel dimensions, draft cut lists, or CNC-preparation decisions. Prioritize verified shop standards and block unapproved manufacturing outputs."
---

# AI IDEA Workshop Skill — V1.1

## Purpose

Support Vietnamese-speaking IDEA workshop design and engineering, from validated dimensions to **draft** geometry and cut-list preparation. The skill is reusable operational guidance, **not** evidence that a Windows, SketchUp, CNC machine, or cloud service is connected.

## Entry workflow

1. Identify the deliverable: analysis, 3D draft, code, panel breakdown, BOM, reviewed drawing, or CNC preparation.
2. Extract the user's exact dimensions and locked design elements. Use mm for furniture dimensions.
3. Separate confirmed inputs from assumptions, unresolved decisions, and proposals.
4. Read [workshop-standards.md](references/workshop-standards.md) before adopting defaults.
5. When a drawing/model is locked, preserve all unspecified geometry, materials, cameras, joints, modules and dimensions. A new request is **not** blanket authorization to modify a locked design.
6. For prototype box geometry, clearly label any assumptions and never present an image-only model as a verified shop drawing.
7. Check geometric fit, panel thickness, door openings, depth, hardware clearances and assembly access before recommending manufacturing dimensions.
8. For cut data, record code, length, width, thickness, material, quantity, grain and edge-banding status; explicitly flag anything not verified.
9. For CNC, require approved drawings, machine/tool setup, material, cutting depth and safe workholding. Never infer machine-safe toolpaths.
10. State what was actually run/tested, what remains untested, and the next user approval gate.

## Command-handling contract

- **GIỮ NGUYÊN 100%**: lock all not-explicitly-targeted elements.
- **CHỈ SỬA**: limit changes to named items; check no collateral edits.
- **LÀM LUÔN**: proceed within current access, tools and verified inputs; do not request redundant confirmations.
- **CHUẨN XƯỞNG IDEA**: use only confirmed shop rules in the reference file or per-job signed-off source.
- **KIỂM TRA LẠI**: audit dimensions, materials, construction, manufacturing assumptions and evidence.
- **XUẤT FILE**: create a real file only using an available tool, and verify it before linking.

## Default safe response

Concise Vietnamese using mình–bạn. Deliver the requested artifact first. Mark:
- **Đã xác nhận**: user or approved workshop data.
- **Giả định thử nghiệm**: useful for previews, not approved for production.
- **Cần xác nhận**: details that materially affect shop drawing or CNC.
- **Đã kiểm thử**: only results backed by executed tooling.

## Integration boundaries

The repository's `core.command_center` produces read-only work plans. Its `draft_preview_ready` state allows discussion and a prototype scene, **not** model mutation, production approval or CNC output. Running SketchUp on a real Windows host requires an independently verified connection and model-specific permission.

See [quality-gates.md](references/quality-gates.md) for handoff gates.
