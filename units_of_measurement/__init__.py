"""Units of measurement dataset — 2,959 units, 121 physical quantities, 11 measurement systems."""

import json
from pathlib import Path

__version__ = "1.0.0"

_PKG_DIR = Path(__file__).resolve().parent
_DATA_DIR = _PKG_DIR / "data"
if not _DATA_DIR.is_dir():
    # Running from the source tree — data lives in json/ at the repo root
    _DATA_DIR = _PKG_DIR.parent / "json"


def load(dataset="units_of_measurement"):
    """Load a units of measurement dataset.

    Args:
        dataset: One of "units_of_measurement" (default), "si_units", or "uom".

    Returns:
        List of dicts, one per unit.
    """
    valid = {"units_of_measurement", "si_units", "uom"}
    if dataset not in valid:
        raise ValueError(
            f"Unknown dataset {dataset!r}. Choose from: {', '.join(sorted(valid))}"
        )
    text = (_DATA_DIR / f"{dataset}.jsonl").read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]
