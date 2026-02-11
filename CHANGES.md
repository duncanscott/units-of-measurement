# Changelog

## v1.3.0

### Ontology Annotations

Each record in `units_of_measurement.jsonl` can now carry cross-references to three standard ontologies. Two new optional fields were added:

- **`external_ids`** — an object containing standardized identifiers:
  - `uo` — [Unit Ontology](http://www.obofoundry.org/ontology/uo.html) CURIE (e.g., `"UO:0000008"` for meter)
  - `ucum` — [UCUM](https://ucum.org/) code (e.g., `"m"` for meter)

- **`ontology_metadata`** — an object containing labels and definitions from:
  - `uo` — Unit Ontology (`label`, `definition`)
  - `om` — [Ontology of units of Measure 2.0](https://github.com/HajoRijgersberg/OM) (`uri`, `label`, `definition`, `ucum_code`)

Coverage out of 2,958 records:

| Source | Records matched |
|--------|-----------------|
| UO     | 229             |
| UCUM   | 1,017           |
| OM     | 1,139           |

The annotation pipeline uses ontology exports stored in `resource/bioportal/` and can be re-run with:

```sh
python3 scripts/annotate_with_ontologies.py
python3 scripts/apply_ontology_annotations.py
```

### JSON Schemas

Added `schema/` directory with [JSON Schema](https://json-schema.org/) (draft 2020-12) definitions for all 10 JSONL datasets. Validate with:

```sh
pip install jsonschema
python3 scripts/validate_schemas.py
```

Two schemas are shared:
- `units_of_measurement.schema.json` validates both `units_of_measurement.jsonl` and `units_with_ontologies.jsonl`
- `focused/si_base_units.schema.json` validates both `si_base_units.jsonl` and `biomedical_units.jsonl`

### Focused Lists

Added `jsonl/focused/` directory with curated subsets derived from the canonical dataset:

- `si_base_units.jsonl` — 8 SI base units with ontology cross-references
- `property_summary.jsonl` — 121 properties with unit counts, systems, and annotation tallies
- `biomedical_units.jsonl` — 1,060 units with UO or UCUM+OM identifiers
- `uo_units.jsonl` — 234 units with Unit Ontology identifiers
- `ucum_units.jsonl` — 1,020 units with UCUM codes and OM metadata

Regenerate with `python3 scripts/generate_focused_lists.py`.

### Additional Files

- `jsonl/units_with_ontologies.jsonl` — intermediate annotated dataset (same schema as canonical, used by the annotation pipeline)
- `jsonl/ontology_crosswalk_base_units.jsonl` — 7 SI base units with full UO/OM/UCUM cross-references and source provenance

### New Scripts

- `annotate_with_ontologies.py` — enrich dataset with UO/OM/UCUM identifiers
- `apply_ontology_annotations.py` — merge annotations into canonical dataset
- `validate_ontology_annotations.py` — QA for annotation coverage
- `validate_schemas.py` — JSON Schema validation for all JSONL files
- `generate_focused_lists.py` — derive focused subsets
- `convert_jsonl_to_json.py` — regenerate `json/` as JSON arrays from JSONL

### Package Contents

Published packages (npm + PyPI) now include:
- 3 API-loadable JSONL files (`units_of_measurement`, `si_units`, `uom`)
- `ontology_crosswalk_base_units.jsonl`
- `focused/` directory (5 files)
- `schema/` directory (9 schemas + README)

Excluded from packages: `units_with_ontologies.jsonl` (intermediate pipeline artifact).

### Fixes

- `validate_uom.py` updated to recognize `external_ids` and `ontology_metadata` fields
- README: fixed code block formatting, documented all new fields and files, added ontology data sources

---

## v1.2.1

- Fixed duplicate PSI entry (property "pressure" appeared twice)
- Removed hardcoded record counts from validator
- Added `(unit, property)` uniqueness check to validator

## v1.2.0

- Added `canonical_unit` field — whitespace-free form using `·` and `/` delimiters with superscript exponents
- Added `quantity` field — mirrors `property` in all entries
- Added `dimension` field — SI base-exponent map (e.g., `{"L": 1, "T": -1}` for velocity)
- Added dimension documentation to README

## v1.1.0

- Added `alternate_unit` field for spelling variants (e.g., `["metre"]` for `"meter"`)
- Fixed `alternate_unit` for prefixed meter units

## v1.0.0

- Initial release: 2,958 units across 121 physical quantities and 11 measurement systems
- Three datasets: `units_of_measurement` (merged), `si_units`, `uom`
- Dual npm/PyPI package with `load()` API
