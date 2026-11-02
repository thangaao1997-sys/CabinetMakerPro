# AI IDEA V1.4 — Windows readiness and manual SketchUp verification

This is a safe preparatory step, **not remote control**.

## What this build checks
- RBZ has exactly the loader and two expected Ruby files, with valid ZIP integrity.
- Optional byte-for-byte parity between RBZ and repository source.
- Host Python version is 3.11 or later.
- Checks the **presence only** of a SketchUp 2025 executable at the standard Windows installation location.
- Reports the likely per-user SketchUp Plugins directory (does **not** copy files there).

## Local command

```powershell
python -m tools.windows_preflight --rbz dist/AI_IDEA_V1_ALPHA.rbz --source-root .
```

A successful preflight does **not** mean the plugin runs correctly inside SketchUp. Your Windows test must:

1. Install the RBZ with SketchUp 2025 → Extension Manager → Install Extension.
2. Enable the extension if necessary.
3. Verify the `AI IDEA - Import DRAFT scene (JSON)` menu entry.
4. Import the sample `examples/scene.json` (five groups within an AI IDEA DRAFT parent).
5. Check group dimensions and the `manufacturing_approved = false` model attribute.
6. Undo and verify the operation reverts cleanly.
7. Share a diagnostic log if the extension fails. Remove private paths, API keys and personal information before sharing.

Do **not** run CNC or treat the five-panel prototype as an approved cutting specification.

## CI
Linux tests validate the package and Python/Ruby logic. A dedicated Windows job validates the preflight code using Windows Python, without requiring SketchUp to be installed on the CI runner.

## Current limitations
- No automatic installation, no elevation, no network listener.
- Detecting `SketchUp.exe` does not prove that SketchUp launched or that the plugin loaded.
- Paths may differ if the user installed SketchUp to a custom location; use an actual smoke test.
