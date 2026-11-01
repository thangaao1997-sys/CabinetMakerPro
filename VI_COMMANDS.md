# AI IDEA: Vietnamese draft-command protocol

## Supported sentence (millimetres)

```text
Tạo tủ bếp rộng 600 mm sâu 560 mm cao 820 mm
Tạo tủ áo rộng 1200 mm sâu 600 mm cao 2400 mm chân 50 mm
```

The parser intentionally supports a small exact grammar and **rejects extra instructions**. It will not silently ignore an edit, CNC request, new dimension or ambiguous furniture type. Non-kitchen cabinets require an explicit base height. There is no AI speech transcription in this module yet.

## Local command

```bash
python -m core.vi_cli --text "Tạo tủ bếp rộng 600 mm sâu 560 mm cao 820 mm"
```

Output includes a validated command, prototype scene, collision audit, and cutting preview. All outputs are marked **NOT APPROVED FOR MANUFACTURING**.

## Automated checks
GitHub Actions runs `python -m unittest discover -s tests -v` along with Ruby parser/mock checks and RBZ packaging.

## Boundaries
- The old workshop standards remain unchanged.
- The nominal base is not actually constructed; prototype assumes a virtual height allocation.
- The full-height sides and overlay back are a **prototype assumption only**.
- No remote iPhone/Windows connection or SketchUp 2025 real-world verification.
- No production CNC output.

## Next milestone
Authenticated Windows bridge, with a manual approval gate before modifying a SketchUp model. Do not enable a public listener or remote access by default.
