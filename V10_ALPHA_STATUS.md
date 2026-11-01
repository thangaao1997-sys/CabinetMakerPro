# AI IDEA V1.0.1-alpha — source synchronized

## GitHub source now available
- `core/`: validated commands, draft parts, collision checks, scene export and preview cutting data
- `bridge.py`: offline file-based command-to-scene converter
- `plugin/ai_idea_v10.rb` + `plugin/ai_idea_v10/`: SketchUp extension entry point and scene importer
- `tests/`: Python unit tests, Ruby parser and mock import tests
- `examples/kitchen_command.json`: 600×560×820 mm draft test case
- `.github/workflows/core-tests.yml`: test workflow configuration

## Local verification (November 1, 2026)
- Python: 28 tests passed in the local environment
- Ruby parser: 6 checks passed
- Ruby mock import: 4 checks passed
- Ruby syntax: all 3 packaged files passed
- Manual CLI smoke test: generated a 5-object scene with manufacturing_approved=false
- RBZ and source ZIP: archive integrity verified

## Unverified deployment
- No GitHub Actions run success confirmed yet.
- No installation or execution inside SketchUp 2025 on Windows confirmed.
- No live iPhone-to-Windows integration.
- No production CNC tooling or approval.

## Safety
The sample configuration assumes overlay back, full-height sides and a virtual base allocation. It is NOT an approved IDEA construction method.
The generated geometry and cutting-preview data are NOT production-ready. The installer requires explicit manual JSON selection.

## Immediate next gates
1. Confirm CI via GitHub Actions page.
2. Smoke-test extension loading in actual SketchUp 2025.
3. Establish authenticated, least-privilege machine communication ONLY when a Windows-side endpoint is available and explicitly connected.
4. Confirm workshop joint construction, back attachment, edges and hardware before enabling production output.
