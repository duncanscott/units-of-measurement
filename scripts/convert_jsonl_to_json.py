"""Convert every JSONL file under jsonl/ into a JSON array under json/."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSONL_DIR = ROOT / "jsonl"
JSON_DIR = ROOT / "json"


def convert_file(src: Path, dst: Path) -> None:
    records = [json.loads(line) for line in src.read_text(encoding="utf-8").splitlines() if line.strip()]
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    count = 0
    for src in JSONL_DIR.rglob("*.jsonl"):
        rel = src.relative_to(JSONL_DIR)
        dst = (JSON_DIR / rel).with_suffix(".json")
        convert_file(src, dst)
        count += 1
    print(f"Converted {count} jsonl files into JSON arrays under {JSON_DIR}")


if __name__ == "__main__":
    main()
