#!/usr/bin/env python3
"""
Extract units from the OM (Ontology of units of Measure) RDF file and match
them against the units_of_measurement.jsonl dataset.

This script:
1. Parses om-2.0.rdf using xml.etree.ElementTree
2. Extracts all unit resources (om:Unit, om:SingularUnit, om:PrefixedUnit,
   om:UnitMultiple, om:UnitDivision, om:UnitExponentiation, om:UnitMultiplication)
3. For each unit: URI, English labels, alternative labels, symbols, prefix info
4. Saves extracted units as JSON
5. Matches OM units against the JSONL dataset by name, symbol, and alternate names
6. Saves match results as JSON

Output files:
  - resource/om_units_extracted.json
  - resource/om_matches.json
"""

import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
RDF_PATH = os.path.join(
    PROJECT_DIR,
    "resource", "bioportal", "units_of_measure_ontology", "om-2.0.rdf"
)
JSONL_PATH = os.path.join(PROJECT_DIR, "jsonl", "units_of_measurement.jsonl")
EXTRACTED_OUTPUT = os.path.join(PROJECT_DIR, "resource", "om_units_extracted.json")
MATCHES_OUTPUT = os.path.join(PROJECT_DIR, "resource", "om_matches.json")

# Namespaces used in the OM RDF file
NS = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "om": "http://www.ontology-of-units-of-measure.org/resource/om-2/",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "dc": "http://purl.org/dc/elements/1.1/",
}

OM_BASE = "http://www.ontology-of-units-of-measure.org/resource/om-2/"

# The element tag names (with full namespace) for unit types
UNIT_TYPE_TAGS = [
    f"{{{NS['om']}}}Unit",
    f"{{{NS['om']}}}SingularUnit",
    f"{{{NS['om']}}}PrefixedUnit",
    f"{{{NS['om']}}}UnitMultiple",
    f"{{{NS['om']}}}UnitDivision",
    f"{{{NS['om']}}}UnitExponentiation",
    f"{{{NS['om']}}}UnitMultiplication",
]

# RDF type URIs for unit classes (used in rdf:type references)
UNIT_TYPE_URIS = {
    f"{OM_BASE}Unit",
    f"{OM_BASE}SingularUnit",
    f"{OM_BASE}PrefixedUnit",
    f"{OM_BASE}UnitMultiple",
    f"{OM_BASE}UnitDivision",
    f"{OM_BASE}UnitExponentiation",
    f"{OM_BASE}UnitMultiplication",
}

# Prefix type tags
PREFIX_TYPE_TAGS = [
    f"{{{NS['om']}}}SIPrefix",
    f"{{{NS['om']}}}BinaryPrefix",
]


def preprocess_rdf(filepath):
    """
    Read the RDF file and resolve XML entity references that
    ElementTree cannot handle natively.

    The OM RDF file uses a DOCTYPE with ENTITY declarations. ElementTree
    does not support external or internal DTD entities, so we must:
    1. Parse the entity definitions from the DOCTYPE
    2. Remove the DOCTYPE
    3. Replace all &entity; references with their resolved values
    """
    with open(filepath, "r", encoding="utf-8-sig") as f:
        content = f.read()

    # Extract entity definitions from DOCTYPE block
    entity_map = {}
    doctype_match = re.search(r"<!DOCTYPE[^[]*\[(.*?)\]>", content, re.DOTALL)
    if doctype_match:
        entity_block = doctype_match.group(1)
        # Match ENTITY declarations (skip commented-out ones)
        # Remove XML comments from the block first
        cleaned_block = re.sub(r"<!--.*?-->", "", entity_block, flags=re.DOTALL)
        for m in re.finditer(
            r'<!ENTITY\s+(\w+)\s+"([^"]*)"\s*>', cleaned_block
        ):
            entity_map[m.group(1)] = m.group(2)
        print(f"  Found {len(entity_map)} entity definitions:")
        for name, value in sorted(entity_map.items()):
            print(f"    &{name}; = {value}")

    # Remove the DOCTYPE declaration entirely
    content = re.sub(r"<!DOCTYPE[^>]*\[.*?\]>", "", content, flags=re.DOTALL)

    # Replace all &entity; references with their values.
    # Do multiple passes in case of nested references (unlikely but safe).
    for _ in range(3):
        changed = False
        for name, value in entity_map.items():
            new_content = content.replace(f"&{name};", value)
            if new_content != content:
                changed = True
                content = new_content
        if not changed:
            break

    # Verify no unresolved custom entities remain
    remaining = re.findall(r"&(\w+);", content)
    # Filter out standard XML entities
    standard = {"amp", "lt", "gt", "quot", "apos"}
    unresolved = [e for e in remaining if e not in standard]
    if unresolved:
        unique_unresolved = sorted(set(unresolved))
        print(f"  WARNING: {len(unique_unresolved)} unresolved entity types remain: {unique_unresolved[:10]}")

    return content


def extract_local_name(uri):
    """Extract the local name from a full URI."""
    if "#" in uri:
        return uri.split("#")[-1]
    if "/" in uri:
        return uri.rsplit("/", 1)[-1]
    return uri


def get_tag_local_name(tag):
    """Extract local name from a namespaced tag like {ns}LocalName."""
    if "}" in tag:
        return tag.split("}")[1]
    return tag


def parse_units(root):
    """
    Parse all unit elements from the RDF tree.

    Units can appear as:
    - Direct typed elements: <om:Unit rdf:about="..."> ... </om:Unit>
    - Or <om:PrefixedUnit>, <om:UnitDivision>, etc.

    The same URI may appear in multiple elements (e.g., metre is defined in
    one element with labels and again in another with comments). We merge them.
    """
    units = {}  # uri -> dict of unit info

    rdf_about = f"{{{NS['rdf']}}}about"
    rdf_resource = f"{{{NS['rdf']}}}resource"
    rdf_type_tag = f"{{{NS['rdf']}}}type"
    rdfs_label_tag = f"{{{NS['rdfs']}}}label"
    xml_lang = "{http://www.w3.org/XML/1998/namespace}lang"
    om_symbol_tag = f"{{{NS['om']}}}symbol"
    om_alt_symbol_tag = f"{{{NS['om']}}}alternativeSymbol"
    om_alt_label_tag = f"{{{NS['om']}}}alternativeLabel"
    om_has_prefix_tag = f"{{{NS['om']}}}hasPrefix"
    om_has_factor_tag = f"{{{NS['om']}}}hasFactor"
    om_has_dimension_tag = f"{{{NS['om']}}}hasDimension"
    om_has_unit_tag = f"{{{NS['om']}}}hasUnit"
    om_has_numerator_tag = f"{{{NS['om']}}}hasNumerator"
    om_has_denominator_tag = f"{{{NS['om']}}}hasDenominator"
    om_has_base_tag = f"{{{NS['om']}}}hasBase"
    om_has_exponent_tag = f"{{{NS['om']}}}hasExponent"
    om_has_term1_tag = f"{{{NS['om']}}}hasTerm1"
    om_has_term2_tag = f"{{{NS['om']}}}hasTerm2"
    # Also check for bare (default-namespace) term tags
    bare_has_term1_tag = f"{{{NS['om']}}}hasTerm1"
    bare_has_term2_tag = f"{{{NS['om']}}}hasTerm2"

    def ensure_unit(uri):
        if uri not in units:
            units[uri] = {
                "uri": uri,
                "local_name": extract_local_name(uri),
                "types": set(),
                "labels_en": [],
                "labels_all": {},
                "alternative_labels_en": [],
                "symbols": [],
                "alternative_symbols": [],
                "prefix_uri": None,
                "prefix_name": None,
                "prefix_factor": None,
                "base_unit_uri": None,
                "dimension_uri": None,
                "numerator_uri": None,
                "denominator_uri": None,
                "base_uri": None,
                "exponent": None,
                "term1_uri": None,
                "term2_uri": None,
            }
        return units[uri]

    # Iterate over all elements in the tree
    for elem in root:
        tag = elem.tag

        # Check if this element is a unit type element
        tag_type = None
        for unit_tag in UNIT_TYPE_TAGS:
            if tag == unit_tag:
                tag_type = get_tag_local_name(unit_tag)
                break

        if tag_type is None:
            continue

        uri = elem.get(rdf_about)
        if not uri:
            continue

        unit = ensure_unit(uri)
        unit["types"].add(tag_type)

        # Process child elements
        for child in elem:
            child_tag = child.tag

            # rdf:type - additional type classification
            if child_tag == rdf_type_tag:
                type_uri = child.get(rdf_resource, "")
                if type_uri in UNIT_TYPE_URIS:
                    type_name = extract_local_name(type_uri)
                    unit["types"].add(type_name)

            # rdfs:label
            elif child_tag == rdfs_label_tag:
                lang = child.get(xml_lang, "")
                text = (child.text or "").strip()
                if text:
                    if lang not in unit["labels_all"]:
                        unit["labels_all"][lang] = []
                    if text not in unit["labels_all"][lang]:
                        unit["labels_all"][lang].append(text)
                    if lang == "en" and text not in unit["labels_en"]:
                        unit["labels_en"].append(text)

            # om:alternativeLabel
            elif child_tag == om_alt_label_tag:
                lang = child.get(xml_lang, "")
                text = (child.text or "").strip()
                if text and lang == "en" and text not in unit["alternative_labels_en"]:
                    unit["alternative_labels_en"].append(text)

            # om:symbol
            elif child_tag == om_symbol_tag:
                text = (child.text or "").strip()
                if text and text not in unit["symbols"]:
                    unit["symbols"].append(text)

            # om:alternativeSymbol
            elif child_tag == om_alt_symbol_tag:
                text = (child.text or "").strip()
                if text and text not in unit["alternative_symbols"]:
                    unit["alternative_symbols"].append(text)

            # om:hasPrefix
            elif child_tag == om_has_prefix_tag:
                prefix_uri = child.get(rdf_resource, "")
                if prefix_uri:
                    unit["prefix_uri"] = prefix_uri
                    unit["prefix_name"] = extract_local_name(prefix_uri)

            # om:hasDimension
            elif child_tag == om_has_dimension_tag:
                dim_uri = child.get(rdf_resource, "")
                if dim_uri:
                    unit["dimension_uri"] = dim_uri

            # om:hasUnit (base unit for prefixed units)
            elif child_tag == om_has_unit_tag:
                base_uri = child.get(rdf_resource, "")
                if base_uri:
                    unit["base_unit_uri"] = base_uri

            # om:hasNumerator (for UnitDivision)
            elif child_tag == om_has_numerator_tag:
                num_uri = child.get(rdf_resource, "")
                if num_uri:
                    unit["numerator_uri"] = num_uri

            # om:hasDenominator (for UnitDivision)
            elif child_tag == om_has_denominator_tag:
                den_uri = child.get(rdf_resource, "")
                if den_uri:
                    unit["denominator_uri"] = den_uri

            # om:hasBase (for UnitExponentiation)
            elif child_tag == om_has_base_tag:
                base_uri = child.get(rdf_resource, "")
                if base_uri:
                    unit["base_uri"] = base_uri

            # om:hasExponent (for UnitExponentiation)
            elif child_tag == om_has_exponent_tag:
                text = (child.text or "").strip()
                if text:
                    try:
                        unit["exponent"] = int(text)
                    except ValueError:
                        unit["exponent"] = text

            # hasTerm1 / hasTerm2 (for UnitMultiplication)
            # These may appear with or without namespace prefix
            elif child_tag == om_has_term1_tag or get_tag_local_name(child_tag) == "hasTerm1":
                t1_uri = child.get(rdf_resource, "")
                if t1_uri:
                    unit["term1_uri"] = t1_uri

            elif child_tag == om_has_term2_tag or get_tag_local_name(child_tag) == "hasTerm2":
                t2_uri = child.get(rdf_resource, "")
                if t2_uri:
                    unit["term2_uri"] = t2_uri

    return units


def parse_prefixes(root):
    """Parse prefix definitions (SIPrefix, BinaryPrefix) from the RDF."""
    prefixes = {}
    rdf_about = f"{{{NS['rdf']}}}about"
    rdfs_label_tag = f"{{{NS['rdfs']}}}label"
    xml_lang = "{http://www.w3.org/XML/1998/namespace}lang"
    om_symbol_tag = f"{{{NS['om']}}}symbol"
    om_has_factor_tag = f"{{{NS['om']}}}hasFactor"

    for elem in root:
        is_prefix = False
        for prefix_tag in PREFIX_TYPE_TAGS:
            if elem.tag == prefix_tag:
                is_prefix = True
                break
        if not is_prefix:
            continue

        uri = elem.get(rdf_about)
        if not uri:
            continue

        prefix_info = {
            "uri": uri,
            "name": extract_local_name(uri),
            "type": get_tag_local_name(elem.tag),
            "label_en": None,
            "symbol": None,
            "factor": None,
        }

        for child in elem:
            if child.tag == rdfs_label_tag:
                lang = child.get(xml_lang, "")
                if lang == "en":
                    prefix_info["label_en"] = (child.text or "").strip()
            elif child.tag == om_symbol_tag:
                prefix_info["symbol"] = (child.text or "").strip()
            elif child.tag == om_has_factor_tag:
                prefix_info["factor"] = (child.text or "").strip()

        prefixes[uri] = prefix_info

    return prefixes


def enrich_units_with_prefix_info(units, prefixes):
    """Add prefix factor information to units that reference a prefix."""
    for uri, unit in units.items():
        if unit["prefix_uri"] and unit["prefix_uri"] in prefixes:
            prefix = prefixes[unit["prefix_uri"]]
            unit["prefix_name"] = prefix["name"]
            unit["prefix_factor"] = prefix["factor"]


def serialize_units(units):
    """Convert units dict to a JSON-serializable list."""
    result = []
    for uri, unit in sorted(units.items()):
        entry = dict(unit)
        entry["types"] = sorted(entry["types"])
        result.append(entry)
    return result


def load_jsonl_dataset(path):
    """Load the JSONL dataset."""
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"  Warning: could not parse line {line_num}: {e}")
    return entries


def normalize(s):
    """Normalize a string for case-insensitive matching."""
    if not s:
        return ""
    # Lowercase, strip whitespace
    s = s.lower().strip()
    # Normalize unicode characters for common variants
    s = s.replace("\u00b7", " ")  # middle dot
    s = s.replace("\u00b2", "2")  # superscript 2
    s = s.replace("\u00b3", "3")  # superscript 3
    s = s.replace("\u207b\u00b9", "-1")  # superscript -1
    s = s.replace("\u00b5", "u")  # micro sign -> u
    s = s.replace("\u03bc", "u")  # greek mu -> u
    return s


def build_om_lookup(units_list):
    """
    Build lookup dictionaries from OM units for matching.
    Returns dicts mapping normalized string -> list of OM URIs.
    """
    by_label = defaultdict(set)
    by_symbol = defaultdict(set)
    by_alt_label = defaultdict(set)
    by_alt_symbol = defaultdict(set)
    by_local_name = defaultdict(set)

    for unit in units_list:
        uri = unit["uri"]

        # English labels
        for label in unit.get("labels_en", []):
            by_label[normalize(label)].add(uri)

        # Alternative English labels
        for alt_label in unit.get("alternative_labels_en", []):
            by_alt_label[normalize(alt_label)].add(uri)

        # Symbols
        for sym in unit.get("symbols", []):
            by_symbol[normalize(sym)].add(uri)

        # Alternative symbols
        for alt_sym in unit.get("alternative_symbols", []):
            by_alt_symbol[normalize(alt_sym)].add(uri)

        # Local name from URI (e.g., "metre", "squareMetre")
        local = unit.get("local_name", "")
        if local:
            by_local_name[normalize(local)].add(uri)

    return {
        "label": by_label,
        "alt_label": by_alt_label,
        "symbol": by_symbol,
        "alt_symbol": by_alt_symbol,
        "local_name": by_local_name,
    }


def match_dataset_to_om(jsonl_entries, om_lookup):
    """
    Match each JSONL entry against the OM units.
    Returns a list of match result dicts and summary statistics.
    """
    matches = []
    matched_count = 0
    unmatched_count = 0

    for entry in jsonl_entries:
        unit_name = entry.get("unit", "")
        canonical = entry.get("canonical_unit", "")
        symbol = entry.get("symbol", "")
        plural = entry.get("plural", "")
        alternates = entry.get("alternate_unit", [])
        if alternates is None:
            alternates = []

        # Collect all candidate strings to try matching
        candidates = []
        if unit_name:
            candidates.append(("unit_name", unit_name))
        if canonical:
            candidates.append(("canonical_unit", canonical))
        if symbol:
            candidates.append(("symbol", symbol))
        if plural:
            candidates.append(("plural", plural))
        for alt in alternates:
            candidates.append(("alternate_unit", alt))

        found_uris = {}  # uri -> set of match_methods

        for source, value in candidates:
            norm_val = normalize(value)
            if not norm_val:
                continue

            # Try matching against each lookup
            for lookup_name, lookup_dict in om_lookup.items():
                if norm_val in lookup_dict:
                    for uri in lookup_dict[norm_val]:
                        if uri not in found_uris:
                            found_uris[uri] = set()
                        found_uris[uri].add(f"{source}->{lookup_name}")

        if found_uris:
            matched_count += 1
            match_entry = {
                "unit": unit_name,
                "symbol": symbol,
                "canonical_unit": canonical,
                "property": entry.get("property", ""),
                "system": entry.get("system", ""),
                "om_matches": [
                    {
                        "uri": uri,
                        "match_methods": sorted(methods),
                    }
                    for uri, methods in sorted(found_uris.items())
                ],
            }
            matches.append(match_entry)
        else:
            unmatched_count += 1

    return matches, matched_count, unmatched_count


def main():
    print("=" * 70)
    print("OM RDF Unit Extraction and Matching")
    print("=" * 70)

    # Step 1: Parse the RDF file
    print(f"\n[Step 1] Parsing RDF file: {RDF_PATH}")
    if not os.path.exists(RDF_PATH):
        print(f"  ERROR: RDF file not found at {RDF_PATH}")
        sys.exit(1)

    xml_content = preprocess_rdf(RDF_PATH)
    root = ET.fromstring(xml_content)
    print(f"  Parsed RDF root element: {root.tag}")
    print(f"  Total child elements in root: {len(root)}")

    # Step 2: Extract prefixes
    print("\n[Step 2] Extracting prefix definitions...")
    prefixes = parse_prefixes(root)
    print(f"  Found {len(prefixes)} prefix definitions")
    for uri, p in sorted(prefixes.items()):
        print(f"    {p['name']:12s}  symbol={p['symbol']}  factor={p['factor']}")

    # Step 3: Extract units
    print("\n[Step 3] Extracting unit definitions...")
    units = parse_units(root)
    enrich_units_with_prefix_info(units, prefixes)
    print(f"  Found {len(units)} unique unit URIs")

    # Count by type
    type_counts = defaultdict(int)
    for uri, unit in units.items():
        for t in unit["types"]:
            type_counts[t] += 1
    print("  Unit counts by type:")
    for t, count in sorted(type_counts.items()):
        print(f"    {t:25s}: {count}")

    # Count units with labels, symbols
    with_labels = sum(1 for u in units.values() if u["labels_en"])
    with_symbols = sum(1 for u in units.values() if u["symbols"])
    with_alt_labels = sum(1 for u in units.values() if u["alternative_labels_en"])
    with_alt_symbols = sum(1 for u in units.values() if u["alternative_symbols"])
    print(f"  Units with English labels:       {with_labels}")
    print(f"  Units with symbols:              {with_symbols}")
    print(f"  Units with alternative labels:   {with_alt_labels}")
    print(f"  Units with alternative symbols:  {with_alt_symbols}")

    # Save extracted units
    units_list = serialize_units(units)
    print(f"\n[Step 4] Saving extracted units to: {EXTRACTED_OUTPUT}")
    with open(EXTRACTED_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(
            {
                "source": RDF_PATH,
                "total_units": len(units_list),
                "prefixes": {
                    uri: {k: v for k, v in p.items()}
                    for uri, p in sorted(prefixes.items())
                },
                "units": units_list,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"  Saved {len(units_list)} units")

    # Step 5: Load JSONL dataset
    print(f"\n[Step 5] Loading JSONL dataset: {JSONL_PATH}")
    jsonl_entries = load_jsonl_dataset(JSONL_PATH)
    print(f"  Loaded {len(jsonl_entries)} entries")

    # Step 6: Build OM lookup and match
    print("\n[Step 6] Building OM lookup indices...")
    om_lookup = build_om_lookup(units_list)
    print(f"  Label index entries:       {len(om_lookup['label'])}")
    print(f"  Alt label index entries:   {len(om_lookup['alt_label'])}")
    print(f"  Symbol index entries:      {len(om_lookup['symbol'])}")
    print(f"  Alt symbol index entries:  {len(om_lookup['alt_symbol'])}")
    print(f"  Local name index entries:  {len(om_lookup['local_name'])}")

    print("\n[Step 7] Matching JSONL entries against OM units...")
    matches, matched_count, unmatched_count = match_dataset_to_om(
        jsonl_entries, om_lookup
    )
    total = matched_count + unmatched_count

    print(f"\n  Results:")
    print(f"  Total JSONL entries:   {total}")
    print(f"  Matched to OM:         {matched_count} ({100*matched_count/total:.1f}%)")
    print(f"  Unmatched:             {unmatched_count} ({100*unmatched_count/total:.1f}%)")

    # Break down matches by method
    method_counts = defaultdict(int)
    for m in matches:
        for om_match in m["om_matches"]:
            for method in om_match["match_methods"]:
                method_counts[method] += 1
    print(f"\n  Match method breakdown (some entries match multiple ways):")
    for method, count in sorted(method_counts.items(), key=lambda x: -x[1]):
        print(f"    {method:40s}: {count}")

    # Break down matches by property/quantity
    matched_by_property = defaultdict(int)
    unmatched_by_property = defaultdict(int)
    matched_set = {m["unit"] for m in matches}
    for entry in jsonl_entries:
        prop = entry.get("property", "unknown")
        if entry["unit"] in matched_set:
            matched_by_property[prop] += 1
        else:
            unmatched_by_property[prop] += 1

    # Save match results
    print(f"\n[Step 8] Saving match results to: {MATCHES_OUTPUT}")

    # Build list of unmatched entries for reference
    unmatched_units = []
    matched_unit_names = {m["unit"] for m in matches}
    for entry in jsonl_entries:
        if entry["unit"] not in matched_unit_names:
            unmatched_units.append({
                "unit": entry["unit"],
                "symbol": entry.get("symbol", ""),
                "canonical_unit": entry.get("canonical_unit", ""),
                "property": entry.get("property", ""),
                "system": entry.get("system", ""),
            })

    match_results = {
        "summary": {
            "total_jsonl_entries": total,
            "matched_count": matched_count,
            "unmatched_count": unmatched_count,
            "match_percentage": round(100 * matched_count / total, 2),
            "total_om_units": len(units_list),
        },
        "match_method_counts": dict(
            sorted(method_counts.items(), key=lambda x: -x[1])
        ),
        "matched_by_property": dict(
            sorted(matched_by_property.items(), key=lambda x: -x[1])
        ),
        "unmatched_by_property": dict(
            sorted(unmatched_by_property.items(), key=lambda x: -x[1])
        ),
        "matches": matches,
        "unmatched_entries": unmatched_units,
    }

    with open(MATCHES_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(match_results, f, indent=2, ensure_ascii=False)
    print(f"  Saved match results ({matched_count} matched, {unmatched_count} unmatched)")

    # Print some example matches
    print("\n[Examples] First 10 matched entries:")
    for m in matches[:10]:
        uris = [om["uri"] for om in m["om_matches"]]
        methods = set()
        for om in m["om_matches"]:
            methods.update(om["match_methods"])
        print(f"  {m['unit']:30s} -> {uris[0]}")
        print(f"    via: {', '.join(sorted(methods))}")

    # Print some unmatched
    print(f"\n[Examples] First 10 unmatched entries:")
    for u in unmatched_units[:10]:
        print(f"  {u['unit']:30s}  symbol={u['symbol']:10s}  property={u['property']}")

    print("\nDone.")


if __name__ == "__main__":
    main()
