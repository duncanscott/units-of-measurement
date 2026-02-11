# Notes to Self

- Synced `json/units_of_measurement.json` with the canonical JSONL after adding `canonical_unit`, `quantity`, and `dimension` fields per the user's follow-up request.
- Updated README examples/tables to show the new metadata so downstream consumers know about deterministic canonical names and SI dimension vectors.
- Reminder: future changes should continue to treat `jsonl/` as the source of truth, regenerate derived JSON before release, and note any additional guidance from the user in this file.
