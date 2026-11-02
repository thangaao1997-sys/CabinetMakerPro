# AI IDEA V1.5 — Read-only SketchUp diagnostics (alpha)

## What changed

- The SketchUp extension now includes an additional menu item:
  **Extensions → AI IDEA - Diagnostics (READ ONLY)**.
- The diagnostic checks SketchUp's reported version, Ruby version, and whether
  a self-contained sample JSON scene can be parsed without changing geometry.
- It does **not** call `add_group`, `start_operation`, `pushpull` or any CNC API.
- After showing the result, the user may choose to save a **sanitized JSON** report;
  cancelling the save dialog writes nothing.
- The extension loader and importer retain their existing behavior.
- The source → RBZ parity checker expects four Ruby members (loader, main,
  importer, diagnostics).

## GitHub verification

- Workflow [run #93](https://github.com/thangaao1997-sys/CabinetMakerPro/actions/runs/41332368970)
- Linux: success, 88 Python tests passed, 7 diagnostic mock assertions, 3
  menu registration mock checks, Ruby syntax checks and reproducible RBZ build.
- Windows: success, 88 Python tests, RBZ verification, Windows starter ZIP
  build and `AI_IDEA_CHECK.cmd` smoke test.
- Artifact: `AI_IDEA_V15_WINDOWS_STARTER` (GitHub Actions #93).
- Existing Python unit tests and workshop defaults remain unchanged.

## How to test on the user's real Windows PC

1. Extract the GitHub Actions artifact, then the inner Windows starter ZIP.
2. Run `AI_IDEA_CHECK.cmd` if Python 3.11+ is installed and on PATH.
3. In SketchUp 2025, install the bundled RBZ via Extension Manager.
4. Enable the extension if necessary.
5. In an empty test model, run **AI IDEA - Diagnostics (READ ONLY)**.
6. Confirm the message shows SketchUp/Ruby versions and `JSON parser: OK`.
7. Optional: save the JSON report after choosing a location yourself.
8. Independently test manual DRAFT JSON import, inspect Group dimensions,
   and verify Undo. This second action **does** modify the test model.
9. Never test imports in an irreplaceable or production model.

## Still unverified

No real SketchUp 2025 session has been run by the assistant.
The diagnostic's UI and file-save behavior are tested with Ruby mocks only.
There is no remote iPhone-to-Windows connection, no machine control, and no
approved manufacturing/cutting/CNC output.
