"""Propagate ontology annotations into jsonl/units_of_measurement.jsonl."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    base_path = root / "jsonl" / "units_of_measurement.jsonl"
    annotated_path = root / "jsonl" / "units_with_ontologies.jsonl"

    annotated_records = load_jsonl(annotated_path)
    annotations: Dict[Tuple[str, str], dict] = {}
    for record in annotated_records:
        key = (record.get("unit"), record.get("property"))
        annotations[key] = record

    output_lines = []
    changed = 0
    for line in base_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            output_lines.append(line)
            continue
        record = json.loads(line)
        key = (record.get("unit"), record.get("property"))
        source = annotations.get(key)
        if not source:
            output_lines.append(line)
            continue
        updated = False
        for field in ("external_ids", "ontology_metadata"):
            value = source.get(field)
            if value and record.get(field) != value:
                record[field] = value
                updated = True
        if updated:
            changed += 1
            output_lines.append(json.dumps(record, ensure_ascii=False))
        else:
            output_lines.append(line)

    base_path.write_text("\n".join(output_lines) + "\n", encoding="utf-8")
    print(f"Updated {changed} records in {base_path}")


if __name__ == "__main__":
    main()
