# AI IDEA Core — development branch

## Purpose
Validate structured cabinet requests before future SketchUp geometry generation.

- Python standard library only.
- Validated values use millimeters.
- Kitchen plinth is 100 mm by default; other cabinet bases must be explicit.
- Confirmed common panel thickness 17 mm, back panel 7 mm.
- `manufacturing_approved` is always false. **Do not run CNC from these commands.**
- No SketchUp connection, automated installation, or production cutting-list generation yet.

## Run tests
```sh
python -m unittest discover -s tests -v
```

## Example
See `examples/kitchen_600.json`.

This branch preserves the existing `main` README.
