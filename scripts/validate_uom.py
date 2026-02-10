# Validate jsonl/units_of_measurement.jsonl
#
# Runs lightweight structural checks on the canonical dataset:
#   * valid JSON Lines with a trailing newline
#   * unique (unit, property) pairs
#   * required fields (unit, canonical_unit, symbol, property, quantity,
#     dimension, conversion_factor, reference_unit, system)
#   * well-formed optional fields (prefix, plural, conversion_offset,
#     alternate_unit)
#   * measurement system is one of the values documented in README.md
#   * canonical_unit contains `·`/`/` delimiters instead of bare spaces
#   * dimension uses SI base/exponential keys (L, M, T, I, Θ, N, J)
#
# Usage:
#   python3 scripts/validate_uom.py

from __future__ import annotations

import json
import sys
from pathlib import Path
from collections import Counter
from typing import Dict, Iterable, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = REPO_ROOT / "jsonl" / "units_of_measurement.jsonl"

MEASUREMENT_SYSTEMS = {
    "SI",
    "Metric",
    "Imperial",
    "CGS",
    "Nautical",
    "Astronomical",
    "Atomic/Natural",
    "IEC",
    "Information",
    "Ancient Roman",
    "other",
}

DIMENSION_KEYS = {"L", "M", "T", "I", "Θ", "N", "J"}

REQUIRED_FIELDS = [
    "unit",
    "canonical_unit",
    "symbol",
    "property",
    "quantity",
    "dimension",
    "conversion_factor",
    "reference_unit",
    "system",
]

OPTIONAL_FIELDS = {"prefix", "plural", "conversion_offset", "alternate_unit"}


class ValidationError(Exception):
    """Raised when the dataset violates a constraint."""


def load_jsonl(path: Path) -> list[dict]:
    problems: list[str] = []
    data: list[dict] = []

    raw = path.read_bytes()
    if not raw.endswith(b"\n"):
        problems.append("file must end with a newline")

    for idx, line in enumerate(raw.splitlines(), start=1):
        text = line.decode("utf-8").strip()
        if not text:
            continue
        try:
            obj = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
        except json.JSONDecodeError as exc:
            problems.append(f"line {idx}: invalid JSON ({exc})")
            continue
        except ValidationError as exc:
            problems.append(f"line {idx}: {exc}")
            continue
        data.append(obj)

    if problems:
        raise ValidationError("; ".join(problems))
    return data


def _reject_duplicate_keys(pairs: Iterable[Tuple[str, object]]) -> Dict[str, object]:
    seen: Dict[str, object] = {}
    for key, value in pairs:
        if key in seen:
            raise ValidationError(f"duplicate key '{key}'")
        seen[key] = value
    return seen


def validate_dataset(records: list[dict]) -> list[str]:
    errors: list[str] = []

    pair_counts = Counter((r.get("unit"), r.get("property")) for r in records)
    for (unit, prop), count in pair_counts.items():
        if count > 1:
            errors.append(
                f"duplicate (unit, property) pair: (\"{unit}\", \"{prop}\") appears {count} times"
            )

    for index, record in enumerate(records, start=1):
        missing = [field for field in REQUIRED_FIELDS if field not in record]
        if missing:
            errors.append(
                f"line {index}: missing required fields: {', '.join(missing)}"
            )

        unexpected = record.keys() - set(REQUIRED_FIELDS) - OPTIONAL_FIELDS
        if unexpected:
            errors.append(
                f"line {index}: unexpected fields: {', '.join(sorted(unexpected))}"
            )

        errors.extend(_validate_field_types(index, record))

    return errors


def _validate_field_types(index: int, record: dict) -> list[str]:
    errors: list[str] = []

    def require_str(field: str, allow_empty: bool = False) -> None:
        value = record.get(field)
        if not isinstance(value, str) or (not value.strip() and not allow_empty):
            errors.append(f"line {index}: {field} must be a non-empty string")

    require_str("unit")
    require_str("canonical_unit")
    require_str("symbol")
    require_str("property")
    require_str("quantity")
    require_str("reference_unit")

    if record.get("quantity") != record.get("property"):
        errors.append(
            f"line {index}: quantity must match property (saw {record.get('quantity')!r} "
            f"vs {record.get('property')!r})"
        )

    canonical_unit = record.get("canonical_unit", "")
    if not isinstance(canonical_unit, str) or not canonical_unit.strip():
        errors.append(f"line {index}: canonical_unit must be a non-empty string")
    elif any(ch.isspace() for ch in canonical_unit):
        errors.append(f"line {index}: canonical_unit must not contain whitespace")

    system = record.get("system")
    if system not in MEASUREMENT_SYSTEMS:
        errors.append(
            f"line {index}: system '{system}' is not recognized "
            f"(expected one of: {', '.join(sorted(MEASUREMENT_SYSTEMS))})"
        )

    cf = record.get("conversion_factor")
    if not isinstance(cf, (int, float)):
        errors.append(f"line {index}: conversion_factor must be numeric")
    elif cf == 0:
        errors.append(f"line {index}: conversion_factor must be non-zero")

    if "conversion_offset" in record:
        offset = record["conversion_offset"]
        if not isinstance(offset, (int, float)):
            errors.append(
                f"line {index}: conversion_offset must be numeric when present"
            )

    if "prefix" in record and record["prefix"] is not None:
        if not isinstance(record["prefix"], str):
            errors.append(f"line {index}: prefix must be a string or null")

    if "plural" in record and record["plural"] is not None:
        if not isinstance(record["plural"], str) or not record["plural"].strip():
            errors.append(f"line {index}: plural must be a non-empty string")

    if "alternate_unit" in record:
        alt = record["alternate_unit"]
        if not isinstance(alt, list) or any(not isinstance(x, str) for x in alt):
            errors.append(
                f"line {index}: alternate_unit must be a list of strings when present"
            )

    dimension = record.get("dimension")
    if not isinstance(dimension, dict):
        errors.append(f"line {index}: dimension must be an object of base exponents")
    else:
        invalid_keys = [key for key in dimension.keys() if key not in DIMENSION_KEYS]
        if invalid_keys:
            errors.append(
                f"line {index}: dimension keys {invalid_keys} are not in {sorted(DIMENSION_KEYS)}"
            )
        for key, value in dimension.items():
            if not isinstance(value, (int, float)):
                errors.append(
                    f"line {index}: dimension exponent for {key} must be numeric"
                )

    return errors


def main() -> int:
    try:
        records = load_jsonl(DATASET_PATH)
    except ValidationError as exc:
        print(f"Validation failed: {exc}")
        return 1

    problems = validate_dataset(records)
    if problems:
        print("Validation failed:")
        for issue in problems:
            print(f"  - {issue}")
        return 1

    print(f"jsonl/units_of_measurement.jsonl looks good ({len(records)} records).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
