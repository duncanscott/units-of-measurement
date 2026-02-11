"""QA script for ontology annotations in units_with_ontologies.jsonl."""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List


def normalize(text: str | None) -> str | None:
    if not text:
        return None
    text = unicodedata.normalize("NFKC", text).lower()
    return text.strip()


def tokenize(text: str | None) -> set[str]:
    if not text:
        return set()
    cleaned = re.sub(r"[^a-z0-9]+", " ", text)
    return {token for token in cleaned.split() if token}


def load_records(path: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def qa(records: List[Dict[str, Any]]) -> None:
    totals = Counter()
    uo_mismatch_examples: List[str] = []
    om_missing_ucum: List[str] = []
    ucum_without_om: List[str] = []
    property_synonyms = {
        "radioactivity": {"activity (of a radionuclide)", "activity"},
        "mass concentration": {
            "gram per milliliter",
            "gram per litre",
            "gram per liter",
            "mass concentration",
        },
        "molar concentration": {"molar concentration", "mole per litre", "mole per liter"},
        "heat flux density": {"heat flux", "heat flow density"},
        "thermal conductivity": {"thermal conductivity", "heat flow density"},
        "illuminance": {"illuminance", "light intensity"},
        "inductance": {"inductance"},
        "ratio": {"ratio", "parts per", "proportion"},
    }

    for record in records:
        ids = record.get("external_ids") or {}
        metadata = record.get("ontology_metadata") or {}
        has_uo = "uo" in ids
        has_ucum = "ucum" in ids
        has_om = "om" in metadata

        totals["total"] += 1
        totals["uo" if has_uo else "uo_missing"] += 1
        totals["ucum" if has_ucum else "ucum_missing"] += 1
        totals["om" if has_om else "om_missing"] += 1

        if has_ucum and not has_om:
            ucum_without_om.append(record["unit"])

        if has_om and has_ucum:
            om_ucum = metadata["om"].get("ucum_code")
            if om_ucum and om_ucum != ids["ucum"]:
                om_missing_ucum.append(f"{record['unit']} ({om_ucum} vs {ids['ucum']})")

        if has_uo:
            prop = normalize(record.get("property"))
            label = metadata.get("uo", {}).get("label") if metadata.get("uo") else None
            definition = metadata.get("uo", {}).get("definition") if metadata.get("uo") else None
            if prop:
                corpus_tokens = tokenize(label) | tokenize(definition)
                allowed = set()
                for phrase in property_synonyms.get(prop, set()):
                    allowed.update(tokenize(phrase))
                target_tokens = set(prop.split()) | allowed
                matches = bool(corpus_tokens & target_tokens)
                if not matches and len(uo_mismatch_examples) < 10:
                    uo_mismatch_examples.append(f"{record['unit']} -> property '{prop}' not mentioned")

    print("=== Annotation Coverage ===")
    print(f"Total records: {totals['total']}")
    print(f"UO matches: {totals['uo']} (missing: {totals['uo_missing']})")
    print(f"UCUM matches: {totals['ucum']} (missing: {totals['ucum_missing']})")
    print(f"OM matches: {totals['om']} (missing: {totals['om_missing']})")

    print("\n=== Potential Issues ===")
    print(f"UCUM present but missing OM metadata: {len(ucum_without_om)}")
    if ucum_without_om:
        print("  e.g. ", ", ".join(ucum_without_om[:5]))
    print(f"OM metadata UCUM mismatch: {len(om_missing_ucum)}")
    if om_missing_ucum:
        print("  e.g. ", "; ".join(om_missing_ucum[:5]))
    print(f"UO property mismatch samples ({len(uo_mismatch_examples)} shown):")
    for sample in uo_mismatch_examples:
        print("  -", sample)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "jsonl" / "units_with_ontologies.jsonl"
    records = load_records(path)
    qa(records)


if __name__ == "__main__":
    main()
