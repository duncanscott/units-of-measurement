#!/usr/bin/env python3
"""
Combine UO and OM ontology mappings with the units-of-measurement dataset.

Merges UO match results and OM match results into the main dataset, producing
an enriched JSONL file with ontology identifiers (UO URI, UO ID, OM URI, UCUM code)
added to each entry where available.

Also parses the OM UCUM TTL file to resolve OM URIs to UCUM codes.
"""

import json
import re
import sys
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR / "jsonl" / "units_of_measurement.jsonl"
UO_MATCHES_PATH = BASE_DIR / "resource" / "uo_matches.json"
OM_MATCHES_PATH = BASE_DIR / "resource" / "om_matches.json"
UCUM_TTL_PATH = Path.home() / "git-hub" / "HajoRijgersberg" / "OM" / "om-2-ucum.ttl"
OUTPUT_PATH = BASE_DIR / "resource" / "units_of_measurement_with_ontology_ids.jsonl"

OM_PREFIX = "http://www.ontology-of-units-of-measure.org/resource/om-2/"


def load_dataset(path):
    """Load the JSONL dataset, returning a list of dicts."""
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def load_uo_matches(path):
    """
    Load UO match results. Returns a dict keyed by (unit, symbol) -> {uo_uri, uo_id}.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    lookup = {}
    for match in data["matches"]:
        key = (match["unit"], match["symbol"])
        lookup[key] = {
            "uo_uri": match.get("match_uo_uri"),
            "uo_id": match.get("match_uo_id"),
        }
    return lookup


def load_om_matches(path):
    """
    Load OM match results. Returns a dict keyed by (unit, symbol) -> {om_uri}.
    Takes the first OM match URI for each entry (most relevant).
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    lookup = {}
    for match in data["matches"]:
        key = (match["unit"], match["symbol"])
        om_matches = match.get("om_matches", [])
        if om_matches:
            # Take the first match URI (most relevant based on match method count)
            lookup[key] = {
                "om_uri": om_matches[0]["uri"],
            }
    return lookup


def parse_ucum_ttl(path):
    """
    Parse the OM UCUM TTL file to extract OM URI -> UCUM code mappings.

    The TTL file uses blocks like:
        om:ampere
          skos:notation "A"^^qudt:UCUMcs ;
        .

    Some entries have multiple notations; we take the first one encountered.
    Returns a dict: full OM URI -> UCUM code string.
    """
    uri_to_ucum = {}
    current_local_name = None

    # Pattern to match an om: subject line (e.g., "om:ampere")
    subject_pattern = re.compile(r"^(om:\S+)\s*$")
    # Pattern to match a skos:notation line with UCUM code
    notation_pattern = re.compile(r'^\s+skos:notation\s+"([^"]+)"\^\^qudt:UCUMcs\s*;')
    # Pattern to match block terminator
    block_end_pattern = re.compile(r"^\.\s*$")

    with open(path, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.rstrip("\n")

            # Check for new subject
            subject_match = subject_pattern.match(line)
            if subject_match:
                local_name = subject_match.group(1)  # e.g., "om:ampere"
                # Strip the "om:" prefix to get the local name
                current_local_name = local_name[3:]
                continue

            # Check for notation
            notation_match = notation_pattern.match(line)
            if notation_match and current_local_name:
                ucum_code = notation_match.group(1)
                full_uri = OM_PREFIX + current_local_name
                # Only keep the first UCUM code per URI
                if full_uri not in uri_to_ucum:
                    uri_to_ucum[full_uri] = ucum_code
                continue

            # Check for block end
            if block_end_pattern.match(line):
                current_local_name = None

    return uri_to_ucum


def main():
    # 1. Load dataset
    print(f"Loading dataset from {DATASET_PATH}...")
    dataset = load_dataset(DATASET_PATH)
    print(f"  Loaded {len(dataset)} entries")

    # 2. Load UO matches
    print(f"Loading UO matches from {UO_MATCHES_PATH}...")
    uo_lookup = load_uo_matches(UO_MATCHES_PATH)
    print(f"  Loaded {len(uo_lookup)} UO matches")

    # 3. Load OM matches
    print(f"Loading OM matches from {OM_MATCHES_PATH}...")
    om_lookup = load_om_matches(OM_MATCHES_PATH)
    print(f"  Loaded {len(om_lookup)} OM matches")

    # 4. Parse UCUM TTL
    print(f"Parsing UCUM TTL from {UCUM_TTL_PATH}...")
    ucum_lookup = parse_ucum_ttl(UCUM_TTL_PATH)
    print(f"  Parsed {len(ucum_lookup)} OM URI -> UCUM code mappings")

    # 5. Enrich each dataset entry
    print("Enriching dataset entries...")
    count_uo = 0
    count_om = 0
    count_ucum = 0
    count_both = 0
    count_any = 0
    count_none = 0

    enriched = []
    for entry in dataset:
        key = (entry["unit"], entry["symbol"])

        # Start with all original fields
        record = dict(entry)

        # Add UO fields
        uo_info = uo_lookup.get(key)
        record["uo_uri"] = uo_info["uo_uri"] if uo_info else None
        record["uo_id"] = uo_info["uo_id"] if uo_info else None

        # Add OM fields
        om_info = om_lookup.get(key)
        om_uri = om_info["om_uri"] if om_info else None
        record["om_uri"] = om_uri

        # Add UCUM code (resolved from OM URI)
        record["ucum_code"] = ucum_lookup.get(om_uri) if om_uri else None

        enriched.append(record)

        # Statistics
        has_uo = record["uo_uri"] is not None
        has_om = record["om_uri"] is not None
        has_ucum = record["ucum_code"] is not None

        if has_uo:
            count_uo += 1
        if has_om:
            count_om += 1
        if has_ucum:
            count_ucum += 1
        if has_uo and has_om:
            count_both += 1
        if has_uo or has_om:
            count_any += 1
        if not has_uo and not has_om:
            count_none += 1

    # 6. Save enriched dataset
    print(f"Saving enriched dataset to {OUTPUT_PATH}...")
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for record in enriched:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"  Wrote {len(enriched)} entries")

    # 7. Print summary statistics
    total = len(dataset)
    print()
    print("=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)
    print(f"Total dataset entries:              {total:>6}")
    print(f"Entries with UO URI:                {count_uo:>6}  ({100 * count_uo / total:.1f}%)")
    print(f"Entries with OM URI:                {count_om:>6}  ({100 * count_om / total:.1f}%)")
    print(f"Entries with UCUM code:             {count_ucum:>6}  ({100 * count_ucum / total:.1f}%)")
    print(f"Entries with both UO and OM:        {count_both:>6}  ({100 * count_both / total:.1f}%)")
    print(f"Entries with at least one ID:       {count_any:>6}  ({100 * count_any / total:.1f}%)")
    print(f"Entries with no ontology mapping:   {count_none:>6}  ({100 * count_none / total:.1f}%)")
    print("=" * 60)


if __name__ == "__main__":
    main()
