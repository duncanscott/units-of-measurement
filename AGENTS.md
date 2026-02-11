# Repository Guidelines

Use this guide to keep `units-of-measurement` changes consistent, verifiable, and easy to review.

## Project Structure & Module Organization
`jsonl/` is the authoritative source (JSON Lines, one object per unit). `json/` mirrors the same data as arrays for consumers that read whole files. `units_of_measurement/` exposes the Python loader backed by `jsonl/` or the packaged `data/` copy, while `index.js` and `index.mjs` implement the CommonJS and ESM entry points. Use `dist/` only for local release tests; legal notices stay in `LICENSE` and `THIRD-PARTY-LICENSES`.

## Build, Test, and Development Commands
- `python -m pip install -e .` keeps the Python loader editable so `from units_of_measurement import load` reflects local JSON edits.
- `python -m build` (Hatchling) builds the wheel/sdist; confirm `units_of_measurement/data/*.jsonl` is bundled before releasing.
- `npm pack` packages the Node entry points with `jsonl/` exactly as npm will ship.
- `node -e "console.log(require('./index.js').load('uom').length)"` is the quick smoke test (expect `2660`); rerun after any data edit.

## Coding Style & Naming Conventions
Python modules target 3.9+, use 4-space indentation, and limit dependencies to the standard library (Pathlib + json). JavaScript keeps `'use strict'`, semicolons, and only core modules; expose a single `load` function that mirrors the Python signature. JSON/JSONL files keep lowercase snake_case keys exactly as documented in `README.md`.

## Testing Guidelines
No formal test suite exists, so every change must be paired with deterministic validation. Confirm record counts with the snippet below, then extend it with assertions required by your update.

```sh
python - <<'PY'
from units_of_measurement import load
assert len(load()) == 2959
assert len(load("si_units")) == 812
assert len(load("uom")) == 2660
PY
```

## Data Validation, Naming Normalization, and Dimensions

When editing unit records or adding new units, prefer improvements that make the dataset verifiable, unambiguous, and machine-safe.

### 1) Keep a deterministic validation script in-repo
Add/maintain a small script (e.g., `scripts/validate_uom.py`) that runs locally and in CI. It should:
- Parse all JSONL files and fail fast on JSON errors / duplicate keys / missing required fields.
- Verify record counts for the exported datasets (`load()`, `load("si_units")`, `load("uom")`) and any other published subsets.
- Verify conversion integrity: `conversion_factor` is numeric and positive, `reference_unit` exists, and the unit/reference pair matches the intended quantity family (or dimension, if present).
- Run cheap sanity checks for common pitfalls (e.g., SI prefixes scaling, inch/foot/yard/mile constants, kg vs g scaling).
- Ensure JSONL formatting stays newline-terminated UTF-8 and that `json/` mirrors `jsonl/` if the project keeps both in sync.

### 2) Normalize naming conventions (canonical unit strings)
Avoid relying on spaces that humans interpret but machines cannot. Prefer a single canonical representation for unit names and symbols:
- Use `·` for multiplication and `/` for division in compound unit names (e.g., `meter·second`, `kilometer/hour`), rather than bare spaces.
- Use singular unit names (e.g., `meter`, not `meters`).
- Prefer explicit prefix/base decomposition when relevant (e.g., store `prefix` + `base_unit` or ensure it can be derived deterministically).
- Keep `symbol` consistent (Unicode) and optionally provide ASCII alternatives (e.g., `µs` plus `us`) for CLI/search compatibility.
- Treat canonical `unit` strings as stable identifiers; store variants as aliases if needed instead of duplicating records.

### 3) Propose a dimension-aware extension (ISO / NIST compatible language)
Optionally extend each record with fields that align with how ISO/IEC 80000 and NIST SP 811 describe quantities and units:
- `quantity`: the kind of quantity (e.g., `length`, `mass`, `time`, `velocity`, `absement`).
- `dimension`: a base-quantity exponent map (e.g., `{ "L": 1, "T": -1 }` for velocity; `{ "L": 1, "T": 1 }` for absement).
This enables:
- Preventing invalid conversions by requiring identical `dimension` vectors (or explicit equivalence rules).
- Catching ambiguities like product vs ratio (`km·h` vs `km/h`) without heuristics.
- Future-proofing derived quantities while keeping the schema minimal and standards-aligned.


## Commit & Pull Request Guidelines
Recent commits use short, descriptive, present-tense summaries (`updated README`, `bump version to 1.1.0`); do the same, referencing affected datasets and the validation commands you ran (Python snippet + Node smoke test). PRs should link issues, list touched `jsonl/` or `json/` files, and call out downstream impacts.

## Data Integrity & Release Tips
Preserve JSON Lines formatting (UTF-8, newline-terminated, no extra commas) so streaming loaders continue working. When units or conversion factors change, update both JSON and JSONL directories, keep counts in sync with the snippet above, bump `__version__` plus `package.json` together, and keep generated archives in `dist/` out of git.
