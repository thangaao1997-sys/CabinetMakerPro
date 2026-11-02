# AI IDEA V1.6–V1.7 — Model safety and read-only dimension audit

## V1.6: import only into a new, empty, unsaved SketchUp model

The extension now refuses a draft import unless:
- The active SketchUp model exists and exposes the required APIs.
- The model has **no saved file path** and the user is not editing inside a component/group.
- The root `model.entities` collection is empty.
- The model does not have `AI_IDEA/design_locked` set.
- The imported file is a regular JSON file (not a symlink) within the 128 KB limit.

If an error occurs during drawing, the importer aborts the SketchUp operation.
No automatic import or remote command is enabled.

**Behavioral note:** Even a brand-new SketchUp template might contain a default scale figure.
Remove it in a new throwaway model, **not** in an existing client design.
The guard is intentionally strict: an already-saved, even-empty client model is not an import target.

## V1.7: verify the selected DRAFT without modifying it

The new menu **Extensions → AI IDEA - Audit selected DRAFT (READ ONLY)**
checks exactly one selected AI IDEA parent group. The importer stores:
- Parent: `scene_schema=ai-idea.scene.v1`, `expected_parts_count`
- Child: `expected_size_mm=[x,y,z]`

The audit verifies that child groups exist, IDs are distinct, and their
axis-aligned bounding-box dimensions match the expected values within
**0.10 mm**. Results are diagnostic, **not** manufacturing approval.
A resized or rotated group may fail, as intended.

## Verification gates

- Ruby mocks verify blank-model import, rejection of existing/saved/locked
  models, and error rollback. 
- Ruby mocks verify dimension agreement, missing/duplicate parts and drift.
- GitHub Actions builds and packages the actual importer/audit Ruby files.

### SketchUp 2025 device check (not yet performed)

1. Open a **new unsaved empty** model (no scale person).
2. Install the RBZ, enable it and run Diagnostics (READ ONLY).
3. Import `examples/scene.json` via **Import DRAFT scene (JSON)**.
4. Select the parent **AI IDEA DRAFT** Group.
5. Run **Audit selected DRAFT (READ ONLY)** and expect PASS.
6. Undo import and confirm no residual geometry.
7. On a separate disposable model, confirm the import is blocked when an
   existing object is present or the model has been saved.
8. Send only non-sensitive diagnostic reports if a failure occurs.

**Do not open or modify production client models for these tests.**

## Limits

No actual SketchUp installation has been accessed by the assistant, and
the CI mocks are not equivalent to an on-device SketchUp verification.
No approved shop drawings, cutting lists, network control or CNC output.
