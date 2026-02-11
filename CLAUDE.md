# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A data distribution package providing comprehensive units of measurement in both JSON and JSONL formats. Published to both npm and PyPI as `units-of-measurement`. No external runtime dependencies — uses only Node.js/Python standard libraries.

Three datasets available in two formats:
- `jsonl/` — JSONL files (one JSON object per line), used by the library's `load()` function
- `json/` — JSON array files (same data, standard JSON format)

Datasets: `units_of_measurement` (merged superset), `si_units` (SI units with all 24 prefixes), `uom` (from Rust `uom` crate, 117 quantities)

## Architecture

The library exposes a single `load(dataset?)` function in both languages that reads a JSONL file and returns an array of unit objects.

- **`index.js`** — CommonJS entry point (`require`)
- **`index.mjs`** — ES Module entry point (`import`)
- **`units_of_measurement/__init__.py`** — Python package entry point

The Python package has a data path fallback: installed packages find data in `units_of_measurement/data/` (mapped via hatch wheel config), while running from source falls back to `jsonl/` at repo root.

## Build & Publish

**No build step.** The library loads JSONL files at runtime.

- **npm:** `package.json` — published files are `jsonl/`, `index.js`, `index.mjs`
- **Python:** `pyproject.toml` with Hatchling build backend — requires Python >=3.9. Wheel maps `jsonl/` → `units_of_measurement/data/`

Validation: `python3 scripts/validate_uom.py` checks the merged JSONL for structural correctness (required fields, types, dimension keys, measurement systems, etc.). No test framework or CI configured.

## JSONL Schema (merged dataset)

Each line is a JSON object with: `unit`, `canonical_unit`, `prefix`, `symbol`, `plural`, `property`, `quantity`, `dimension`, `conversion_factor`, `conversion_offset`, `reference_unit`, `alternate_unit`, `system`. Nullable fields: `prefix`, `conversion_offset`, `alternate_unit`. Temperature conversion formula: `value_in_kelvin = value * conversion_factor + conversion_offset`.

- `canonical_unit` — no-whitespace form using `·` (multiplication) and `/` (division) delimiters, with superscript exponents (e.g., `meter/second²`)
- `quantity` — mirrors `property` in all entries
- `dimension` — SI base-exponent map with keys `L`, `M`, `T`, `I`, `Θ`, `N`, `J`. Only non-zero exponents included. Empty `{}` for dimensionless quantities (angle, solid angle, ratio, information).

## Valid Dataset Names

`"units_of_measurement"`, `"si_units"`, `"uom"` — both JS and Python validate this and throw on invalid input.

## Publishing

Version must be updated in three files: `package.json`, `pyproject.toml`, and `units_of_measurement/__init__.py`.

Workflow:
1. Bump version in all three files
2. Commit version bump and push to `main`
3. Create GitHub release: `gh release create vX.Y.Z --title "vX.Y.Z" --notes "..."`
4. Build and publish to PyPI: `rm -f dist/units_of_measurement-<old>* && python3 -m build && python3 -m twine upload dist/units_of_measurement-X.Y.Z*`
   - Requires `~/.pypirc` with PyPI API token (username `__token__`)
5. Publish to npm: `npm publish --otp=CODE`
   - Requires npm 2FA — ask user for OTP code

Notes:
- Always clean old dist files before building to avoid uploading stale artifacts
- The `json/` directory (JSON arrays) is not included in published packages — only `jsonl/` is shipped
- CLAUDE.md is in `.gitignore` and won't be committed
