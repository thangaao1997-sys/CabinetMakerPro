# AI IDEA V0.9 — Offline draft pipeline

The repository now contains the V0.9 Python pipeline and experimental SketchUp Ruby importer.

## Commands

```bash
python -m unittest discover -s tests -v
ruby -c sketchup/ai_idea_scene_importer.rb
ruby tests/test_scene_parser.rb
python -m core.pipeline examples/kitchen_600.json build/draft
```

The pipeline emits: parts.json, audit.json, scene.json, cutting_preview.json.

## IMPORTANT: not production approved

- All geometry is a **prototype construction**, not confirmed IDEA factory joinery.
- Kitchen base default is 100 mm; other cabinet base must be specified.
- Typical MDF is 17 mm, back panel 7 mm, unless the order specifies otherwise.
- The current generator does not construct a physical base or doors.
- No ChatGPT-to-Windows live bridge exists. The Ruby code is experimental and untested inside actual SketchUp 2025.
- CNC output and production cutlist approval are deliberately disabled.

## Next safety gates

1. Verify GitHub Actions pass.
2. Perform actual SketchUp import smoke test on Windows.
3. Approve concrete joinery/back/base construction before any manufacturing export.
