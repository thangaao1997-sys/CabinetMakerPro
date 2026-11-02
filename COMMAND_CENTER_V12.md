# AI IDEA Command Center V1.2 (read-only)

The local Command Center builds a **work plan** from a strict Vietnamese furniture request. It has **no write-to-model endpoint**, no CNC export, no network server, and no token that implies manufacturing approval.

```bash
python -m core.command_center --text "Tạo tủ bếp rộng 600 mm sâu 560 mm cao 820 mm"
python -m core.command_center --text "Tạo tủ áo rộng 1200 mm sâu 600 mm cao 2400 mm chân 50 mm"
python -m core.command_center --target-model-locked --text "Tạo tủ bếp rộng 600 mm sâu 560 mm cao 820 mm"
```

Statuses:
- `draft_preview_ready`: validated draft geometry and cutting-preview information, no action taken.
- `rejected`: unsupported, ambiguous, unsafe, or invalid command; exit code 2.
- `blocked_locked_design`: existing target locked; no preview or mutation; exit code 2.

Each success includes a SHA-256 fingerprint over the normalized command, 5-panel **prototype** scene, collision audit, and list of pending workshop decisions. The fingerprint only detects changes; **it is not an approval signature**.

AI IDEA Workshop Skill source is in `skills/ai-idea-workshop/`. This repository content is **not automatically installed in the ChatGPT account**. It can be packaged for an explicitly authorized custom plugin later.

Test with `python -m unittest discover -s tests -v`, and verify GitHub Actions before merging. Production outputs stay disabled.
