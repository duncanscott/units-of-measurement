# Scripts Overview

- `annotate_with_ontologies.py` — enriches `jsonl/units_of_measurement.jsonl` with OM/UO/UCUM identifiers using the downloaded ontology exports.
- `apply_ontology_annotations.py` — copies the vetted `external_ids`/`ontology_metadata` fields from `jsonl/units_with_ontologies.jsonl` back into the canonical dataset.
- `generate_focused_lists.py` — derives curated subsets (SI base units, property summary, biomedical, UO-only, UCUM-only) under `jsonl/focused/` directly from the canonical JSONL.
- `validate_ontology_annotations.py` — QA tool that reports coverage and checks property keywords against the UO metadata.
- `convert_jsonl_to_json.py` — regenerates the `json/` directory as JSON arrays that mirror every JSONL file.
- `validate_uom.py` — structural validator for the main dataset (`jsonl/units_of_measurement.jsonl`).

Run these scripts from the repository root (e.g., `python3 scripts/generate_focused_lists.py`).
