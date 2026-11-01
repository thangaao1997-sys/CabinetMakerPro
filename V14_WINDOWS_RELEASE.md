# AI IDEA V1.4 — Windows Starter (verified CI package)

## Verified GitHub Actions result

- Workflow: [AI IDEA validation #74](https://github.com/thangaao1997-sys/CabinetMakerPro/actions/runs/41331926968)
- Commit: `7437dc44271cb50024200d873c6288840d24952e`
- Linux job: **success**, Python + Ruby + ZIP packaging
- Windows job: **success**, **88 Python tests passed**; Windows `AI_IDEA_CHECK.cmd` smoke test passed; Windows starter archive created and uploaded
- Windows artifact name: `AI_IDEA_V14_WINDOWS_STARTER`
- Artifact ID: `13093926945`; outer artifact digest: `sha256:34ba84e54506a624de7f5d248a9cce4b1f4d1f8feb7c9af67e2e98058b5a9082`
- A separate RBZ artifact is available in the same run.

## Bug caught by the Windows test

`SQLiteNonceLedger` used `with sqlite3.connect(...)` to manage a transaction, but that context manager **does not close the database connection**. Windows CI could not remove temporary SQLite databases due to open file handles. Fixed with `contextlib.closing(...)` combined with the transaction context. Re-tested successfully on Windows and Linux. This was a real platform-compatibility regression, not an unverified theory.

## How to obtain the starter

1. Open the [GitHub Actions run #74](https://github.com/thangaao1997-sys/CabinetMakerPro/actions/runs/41331926968) while logged in to GitHub.
2. Under **Artifacts**, download `AI_IDEA_V14_WINDOWS_STARTER`.
3. Extract the GitHub artifact ZIP, and then extract the inner `AI_IDEA_WINDOWS_STARTER.zip`.
4. On Windows, run `AI_IDEA_CHECK.cmd`. It only reads environment and RBZ; it will not install anything.
5. If Python 3.11+ is missing, install it from an official source first (Windows PATH required by this .cmd).
6. Inside SketchUp 2025, use **Extension Manager → Install Extension** to select `AI_IDEA_V1_ALPHA.rbz`.
7. Enable extension if needed, then verify `Extensions → AI IDEA - Import DRAFT scene (JSON)`.
8. Manually import `examples/scene.json`, inspect the 5 groups and check Undo.
9. Report the **specific failure** and a sanitized error log. Do not share tokens, private paths or credentials.

## Safety boundaries

The starter has no admin installation, no network listener, no unattended background process, no control of other user files, no model write on first-run preflight, and no CNC code. Sample cabinet geometry is a **five-panel prototype** with unapproved overlay back and no modeled base. Windows CI uses a runner **without** the customer's SketchUp 2025 installation, so no real CAD compatibility claim can be made.

## Next milestone

V1.5: collect a safe, local diagnostic report from SketchUp 2025; verify model import, dimensions and Undo with explicit user participation. Continue improving offline tests without changing locked workshop dimensions.
