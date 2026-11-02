# AI IDEA V1.8-alpha — Model-integrity audit and Windows starter

**Status:** tested in GitHub-hosted Linux/Windows environments, NOT tested in a real SketchUp 2025 session.

## Purpose

The audit is designed for the IDEA requirement **GIỮ NGUYÊN THIẾT KẾ 100%**. Import is limited to a NEW, UNSAVED, EMPTY SketchUp model. It does not modify any existing client drawing.

The importer now records a baseline at the time of draft import:
- Parent group name, initial transformation matrix, expected part count and schema.
- Child group original name/code, bounding-box size in mm, bounding-box origin in mm and transformation matrix.
- Draft-only `manufacturing_approved=false` flag.

The read-only **Audit selected DRAFT** menu compares:
1. Missing or extra panels and duplicate part codes.
2. Changed parent and child names.
3. Changed panel sizes (X/Y/Z, tolerance 0.10 mm).
4. Shifted panel origins (X/Y/Z, tolerance 0.10 mm).
5. Changed parent and child transformation matrices (translation 0.10 mm; matrix axes 1e-6).

## How to get and test the Windows kit

1. Open the GitHub Actions run linked in the latest PR (branch `develop/ai-idea-core`).
2. Under Artifacts, download **AI_IDEA_V18_WINDOWS_STARTER**. GitHub wraps the deliverable in an outer artifact ZIP.
3. Extract the outer ZIP, then the inner **AI_IDEA_V18_WINDOWS_STARTER.zip**.
4. Run `AI_IDEA_CHECK.cmd`. This reads environment and validates the RBZ, but **does not install** the extension or run SketchUp.
5. Open SketchUp 2025, create a **NEW unsaved EMPTY** test model. Delete the default scale figure if present; never do this in a client project.
6. Install **AI_IDEA_V18_ALPHA.rbz** through Extension Manager and enable it as needed.
7. Run **AI IDEA - Diagnostics (READ ONLY)** and confirm the parser returns OK.
8. Run **AI IDEA - Import DRAFT scene (JSON)** using `examples/scene.json`. Import must refuse saved or nonempty models.
9. Select the **AI IDEA DRAFT** parent Group, then run **Audit selected DRAFT (READ ONLY)** and expect PASS.
10. In a disposable test model, move one component by 2 mm and rerun audit: it should FAIL. Undo and verify it PASSes again.
11. Repeat by moving/rotating the whole parent Group to verify the transform gate.
12. Independently Undo import and verify geometry is removed.

**Do not** use production client models for these tests. Do not run CNC or approve a cut list based on the prototype.

## Security and interpretation

- A passing audit shows that selected bounding boxes and transformations match their stored baseline. It is **not** cryptographic tamper evidence: SketchUp metadata can be edited, and different internal geometry can have the same bounding box.
- Older V1.7 drafts missing origin/transform metadata FAIL CLOSED; reimport with V1.8 into a disposable empty file.
- Bounding-box rotation and SketchUp API behavior must still be verified with SketchUp 2025 in person.
- No 24/7 agent, no network listener, no iPhone-to-Windows remote connection, no production-approved cut data or CNC code.
- MDF 17 mm, back 7 mm, kitchen plinth 100 mm; other cabinet bases are 50 or 17 mm according to approved design. Construction assumptions remain PROTOTYPE ONLY.

## Release acceptance

Only call the build ready for an on-device pilot after:
- GitHub CI passes for both Linux and Windows.
- The RBZ and Windows starter are generated from the same commit.
- SketchUp 2025 manually loads the extension and passes the above checks.

Full shop/manufacturing approval is a separate, later gate.
