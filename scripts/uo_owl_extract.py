#!/usr/bin/env python3
"""
UO OWL Extraction and Matching Script

Parses the Units Ontology (UO) OWL file to extract all unit classes with their
metadata (labels, synonyms, definitions, deprecation status, parent classes),
then matches them against the units-of-measurement dataset using multiple
matching strategies.

Outputs:
  - resource/uo_units_extracted.json  : All extracted UO entries
  - resource/uo_matches.json          : Detailed match results and statistics
"""

import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict, Counter

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)

OWL_FILE = os.path.join(
    os.path.expanduser("~"),
    "git-hub", "bio-ontology-research-group", "unit-ontology", "uo.owl",
)
DATASET_FILE = os.path.join(PROJECT_DIR, "jsonl", "units_of_measurement.jsonl")
EXTRACTED_OUT = os.path.join(PROJECT_DIR, "resource", "uo_units_extracted.json")
MATCHES_OUT = os.path.join(PROJECT_DIR, "resource", "uo_matches.json")

# ---------------------------------------------------------------------------
# XML namespace map
# ---------------------------------------------------------------------------
NS = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "obo": "http://purl.obolibrary.org/obo/",
    "oboInOwl": "http://www.geneontology.org/formats/oboInOwl#",
    "dc": "http://purl.org/dc/elements/1.1/",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
}

UO_URI_PATTERN = re.compile(r"^http://purl\.obolibrary\.org/obo/UO_\d+$")

# Fully-qualified tag names used in the OWL XML
TAG_LABEL = f"{{{NS['rdfs']}}}label"
TAG_SUBCLASS_OF = f"{{{NS['rdfs']}}}subClassOf"
TAG_DEPRECATED = f"{{{NS['owl']}}}deprecated"
TAG_EXACT_SYN = f"{{{NS['oboInOwl']}}}hasExactSynonym"
TAG_RELATED_SYN = f"{{{NS['oboInOwl']}}}hasRelatedSynonym"
TAG_NARROW_SYN = f"{{{NS['oboInOwl']}}}hasNarrowSynonym"
TAG_DEFINITION = f"{{{NS['obo']}}}IAO_0000115"
TAG_RDF_ABOUT = f"{{{NS['rdf']}}}about"
TAG_RDF_RESOURCE = f"{{{NS['rdf']}}}resource"


# ===================================================================
# Part 1: Extract UO entries from the OWL file
# ===================================================================

def extract_uo_entry(element):
    """Extract UO data from an owl:Class or rdf:Description element."""
    uri = element.get(TAG_RDF_ABOUT, "")
    if not UO_URI_PATTERN.match(uri):
        return None

    entry = {
        "uri": uri,
        "id": uri.split("/")[-1],
        "label": None,
        "definition": None,
        "exact_synonyms": [],
        "related_synonyms": [],
        "narrow_synonyms": [],
        "deprecated": False,
        "parent_classes": [],
    }

    for child in element:
        tag = child.tag

        if tag == TAG_LABEL:
            entry["label"] = (child.text or "").strip()

        elif tag == TAG_DEFINITION:
            entry["definition"] = (child.text or "").strip()

        elif tag == TAG_EXACT_SYN:
            text = (child.text or "").strip()
            if text:
                entry["exact_synonyms"].append(text)

        elif tag == TAG_RELATED_SYN:
            text = (child.text or "").strip()
            if text:
                entry["related_synonyms"].append(text)

        elif tag == TAG_NARROW_SYN:
            text = (child.text or "").strip()
            if text:
                entry["narrow_synonyms"].append(text)

        elif tag == TAG_DEPRECATED:
            text = (child.text or "").strip().lower()
            if text == "true":
                entry["deprecated"] = True

        elif tag == TAG_SUBCLASS_OF:
            resource = child.get(TAG_RDF_RESOURCE, "")
            if UO_URI_PATTERN.match(resource):
                entry["parent_classes"].append(resource)

    return entry


def merge_entry(existing, new_entry):
    """Merge a new_entry into an existing entry."""
    if new_entry["label"] and not existing["label"]:
        existing["label"] = new_entry["label"]
    if new_entry["definition"] and not existing["definition"]:
        existing["definition"] = new_entry["definition"]
    existing["exact_synonyms"] = list(set(existing["exact_synonyms"] + new_entry["exact_synonyms"]))
    existing["related_synonyms"] = list(set(existing["related_synonyms"] + new_entry["related_synonyms"]))
    existing["narrow_synonyms"] = list(set(existing["narrow_synonyms"] + new_entry["narrow_synonyms"]))
    existing["parent_classes"] = list(set(existing["parent_classes"] + new_entry["parent_classes"]))
    if new_entry["deprecated"]:
        existing["deprecated"] = True


def parse_uo_owl(owl_path):
    """Parse the UO OWL file and return a list of UO entries."""
    print(f"Parsing OWL file: {owl_path}")
    tree = ET.parse(owl_path)
    root = tree.getroot()

    entries = {}

    # Extract from owl:Class elements
    for cls_elem in root.findall(f"{{{NS['owl']}}}Class"):
        entry = extract_uo_entry(cls_elem)
        if entry:
            uri = entry["uri"]
            if uri in entries:
                merge_entry(entries[uri], entry)
            else:
                entries[uri] = entry

    # Extract from rdf:Description elements (newer UO entries use this form)
    for desc_elem in root.findall(f"{{{NS['rdf']}}}Description"):
        entry = extract_uo_entry(desc_elem)
        if entry:
            uri = entry["uri"]
            if uri in entries:
                merge_entry(entries[uri], entry)
            else:
                entries[uri] = entry

    return list(entries.values())


# ===================================================================
# Part 2: Load dataset
# ===================================================================

def load_dataset(jsonl_path):
    """Load the units-of-measurement JSONL dataset."""
    print(f"Loading dataset: {jsonl_path}")
    records = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


# ===================================================================
# Part 3: Matching logic
# ===================================================================

# UO entries whose labels indicate they are categories/types rather than
# individual units (e.g., "length unit", "mass unit", "prefix", "base unit").
# We still extract them but exclude from matching to avoid false positives.
CATEGORY_LABELS = {
    "unit", "base unit", "prefix",
}

# Regex to detect UO entries that are SI prefix definitions, not units.
PREFIX_LABEL_RE = re.compile(
    r"^(yotta|zetta|exa|peta|tera|giga|mega|kilo|hecto|deca|deka|deci|"
    r"centi|milli|micro|nano|pico|femto|atto|zepto|yocto)$",
    re.IGNORECASE,
)

# UO synonyms that are single-character prefix symbols -- these would cause
# massive false positives if used for symbol matching (e.g., "m" matching
# every unit whose symbol starts with "m").
SINGLE_CHAR_PREFIX_SYMBOLS = set("YZEPTGMkhdcmnfazy")
# Also common ambiguous abbreviations from power-of-ten synonyms
POWER_SYNONYMS_RE = re.compile(r"^10\^\[[-]?\d+\]$")


def is_symbol_like(text):
    """
    Heuristic: is this synonym likely a symbol/abbreviation rather than a
    word-based name?  Symbols tend to be short and contain uppercase or
    special characters.
    """
    if not text:
        return False
    stripped = text.strip()
    # If it contains spaces, it is a name, not a symbol (except for slash-units
    # like "g/m^[2]" which have no spaces)
    if " " in stripped:
        return False
    # Must be reasonably short
    if len(stripped) > 15:
        return False
    # Contains slash, caret, digits, or special chars -> symbol
    if re.search(r"[/\^µ°Ω²³]", stripped):
        return True
    # Mixed case like "mH", "kHz", "Pa" or starts with uppercase like "Gy"
    if re.search(r"[A-Z]", stripped) and len(stripped) <= 10:
        return True
    # All lowercase and very short (e.g., "kg", "mol", "cd", "ppb")
    if len(stripped) <= 5 and stripped.isalpha() and stripped.islower():
        return True
    return False


def symbol_match_is_plausible(dataset_unit_name, uo_entry):
    """
    Validate that a symbol-based match is plausible by cross-checking the
    unit names.  This helps reject false positives like farad (F) matching
    degree Fahrenheit (F), or footlambert (fl) matching femtoliter (fl).

    Returns True if the match seems plausible, False if it looks like a
    coincidental symbol collision.
    """
    uo_label = (uo_entry.get("label") or "").lower()
    unit_lower = dataset_unit_name.lower()

    # Quick check: do the names share a substantial word?
    unit_words = set(re.findall(r"[a-z]{3,}", unit_lower))
    uo_words = set(re.findall(r"[a-z]{3,}", uo_label))

    # Also check synonyms
    all_uo_text = uo_label
    for syn in uo_entry.get("exact_synonyms", []):
        all_uo_text += " " + syn.lower()
    for syn in uo_entry.get("related_synonyms", []):
        all_uo_text += " " + syn.lower()
    uo_words_extended = set(re.findall(r"[a-z]{3,}", all_uo_text))

    shared = unit_words & uo_words_extended
    if shared:
        return True

    # Check if one name is a substring of the other (e.g. "tonne" contains "ton")
    if uo_label in unit_lower or unit_lower in uo_label:
        return True

    # Check if any word from either side is a substring of a word on the other
    for uw in unit_words:
        for ow in uo_words_extended:
            if len(uw) >= 3 and len(ow) >= 3:
                if uw in ow or ow in uw:
                    return True

    # Check the definition for the unit name
    defn = (uo_entry.get("definition") or "").lower()
    for uw in unit_words:
        if len(uw) >= 4 and uw in defn:
            return True

    return False


def normalize_name(text):
    """Normalize a unit name for comparison: lowercase, strip, collapse whitespace."""
    if not text:
        return ""
    text = text.lower().strip()
    # Replace common separators with spaces
    text = text.replace("\u00b7", " ").replace("*", " ").replace("_", " ")
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text)
    return text


def normalize_symbol_for_match(text):
    """
    Normalize a symbol for comparison.  CASE-SENSITIVE because case matters
    for unit symbols (e.g., "m" = metre, "M" = mega).

    Strip outer whitespace only; preserve internal structure so that compound
    symbols like "m/s" stay distinct from "ms".
    """
    if not text:
        return ""
    # Strip outer whitespace
    text = text.strip()
    # Normalize unicode middle-dot and spaces around operators
    text = re.sub(r"\s*\u00b7\s*", "\u00b7", text)  # normalize "m · s" -> "m·s"
    # Remove spaces around slashes
    text = re.sub(r"\s*/\s*", "/", text)
    # Remove spaces around carets
    text = re.sub(r"\s*\^\s*", "^", text)
    # Collapse remaining whitespace to single space (for multi-word symbols we keep them)
    text = re.sub(r"\s+", " ", text)
    return text


def build_uo_lookup(uo_entries):
    """
    Build lookup dictionaries from UO entries for matching.

    Returns:
      - name_map: normalized_name -> list of (UO entry, source_type)
                  where source_type is "label", "exact_synonym", etc.
      - symbol_map: case_sensitive_symbol -> list of (UO entry, source_type)
                    Only populated with synonyms that look like symbols.
    """
    name_map = defaultdict(list)
    symbol_map = defaultdict(list)

    for entry in uo_entries:
        if entry["deprecated"]:
            continue

        label = entry.get("label", "")
        norm_label = normalize_name(label)

        # Skip pure category labels
        if norm_label in CATEGORY_LABELS:
            continue
        # Skip prefix definitions (yotta, zetta, etc.)
        if PREFIX_LABEL_RE.match(norm_label):
            continue

        if norm_label:
            name_map[norm_label].append((entry, "label"))

        all_synonyms = [
            (entry.get("exact_synonyms", []), "exact_synonym"),
            (entry.get("related_synonyms", []), "related_synonym"),
            (entry.get("narrow_synonyms", []), "narrow_synonym"),
        ]

        for syn_list, syn_type in all_synonyms:
            for syn in syn_list:
                syn_stripped = syn.strip()
                if not syn_stripped:
                    continue

                # Skip power-of-ten synonyms like "10^[3]"
                if POWER_SYNONYMS_RE.match(syn_stripped):
                    continue

                norm = normalize_name(syn_stripped)
                if norm:
                    name_map[norm].append((entry, syn_type))

                # If it looks like a symbol, add to symbol_map (case-sensitive)
                if is_symbol_like(syn_stripped):
                    # Skip single-char prefix symbols
                    if len(syn_stripped) == 1 and syn_stripped in SINGLE_CHAR_PREFIX_SYMBOLS:
                        continue
                    sym_norm = normalize_symbol_for_match(syn_stripped)
                    if sym_norm:
                        symbol_map[sym_norm].append((entry, syn_type + "_as_symbol"))

    return name_map, symbol_map


def generate_spelling_variants(text):
    """
    Generate American/British spelling variants of a unit name.
    Returns a set of variant strings (not including the original).
    """
    variants = set()

    swaps = [
        ("meter", "metre"),
        ("metre", "meter"),
        ("liter", "litre"),
        ("litre", "liter"),
        ("deca", "deka"),
        ("deka", "deca"),
    ]

    # Special case: "gram" <-> "gramme", but avoid matching "gramme" inside "programme"
    if "gram" in text and "gramme" not in text and "program" not in text:
        swaps.append(("gram", "gramme"))
    if "gramme" in text:
        swaps.append(("gramme", "gram"))

    for old, new in swaps:
        if old in text:
            variants.add(text.replace(old, new))

    # Generate second-level variants (combine two swaps)
    second_level = set()
    for v in list(variants):
        for old, new in swaps:
            if old in v:
                second_level.add(v.replace(old, new))
    variants.update(second_level)

    variants.discard(text)
    return variants


def try_spelling_variant_match(text, name_map):
    """
    Try to find a match using spelling variants of the given text.
    Returns (entry, method_string) or None.
    """
    for variant in generate_spelling_variants(text):
        if variant in name_map:
            pairs = name_map[variant]
            return pairs[0][0], f"spelling_variant_{pairs[0][1]}", variant, pairs
    return None


def try_per_decomposition_match(text, name_map):
    """
    For compound units like "kilogram per cubic meter", try recombining
    with spelling variants of the numerator and denominator.
    Returns (entry, method_string) or None.
    """
    per_match = re.match(r"^(.+?)\s+per\s+(.+)$", text)
    if not per_match:
        return None

    numerator = per_match.group(1).strip()
    denominator = per_match.group(2).strip()

    num_variants = [numerator] + list(generate_spelling_variants(numerator))
    den_variants = [denominator] + list(generate_spelling_variants(denominator))

    for nv in num_variants:
        for dv in den_variants:
            full = f"{nv} per {dv}"
            if full != text and full in name_map:
                pairs = name_map[full]
                return pairs[0][0], f"per_variant_{pairs[0][1]}", full, pairs
    return None


def try_shape_variant_match(text, name_map):
    """
    For units with "square" or "cubic" prefixes, try spelling variants
    of the base part.
    """
    for prefix in ("square", "cubic"):
        m = re.match(rf"^{prefix}\s+(.+)$", text)
        if m:
            base = m.group(1)
            for variant in generate_spelling_variants(base):
                alt = f"{prefix} {variant}"
                if alt in name_map:
                    pairs = name_map[alt]
                    return pairs[0][0], f"{prefix}_variant_{pairs[0][1]}", alt, pairs
    return None


def match_dataset(dataset, uo_entries):
    """
    Match dataset entries against UO entries using multiple strategies.

    Strategies (in priority order):
      1. unit name -> UO label or synonym (exact, case-insensitive)
      2. symbol -> UO symbol synonyms (case-sensitive, structure-preserving)
      3. plural -> UO label or synonym
      4. alternate_unit entries -> UO label or synonym
      5. canonical_unit -> UO label or synonym
      6. Spelling variant matching (meter/metre, liter/litre, etc.)
      7. Per-decomposition with spelling variants
      8. Square/cubic with spelling variants
    """
    name_map, symbol_map = build_uo_lookup(uo_entries)

    results = []
    matched_count = 0
    method_counts = Counter()

    for record in dataset:
        unit_name = record.get("unit", "")
        symbol = record.get("symbol", "")
        plural = record.get("plural", "")
        canonical = record.get("canonical_unit", "")
        alternates = record.get("alternate_unit", []) or []

        match_info = {
            "unit": unit_name,
            "symbol": symbol,
            "property": record.get("property", ""),
            "quantity": record.get("quantity", ""),
            "system": record.get("system", ""),
            "matched": False,
            "match_method": None,
            "match_uo_uri": None,
            "match_uo_label": None,
            "match_uo_id": None,
            "all_matches": [],
        }

        best = None  # (method, entry)

        # --- Strategy 1: unit name -> UO names (label + synonyms) ---
        norm_unit = normalize_name(unit_name)
        if norm_unit and norm_unit in name_map:
            pairs = name_map[norm_unit]
            # Prefer label matches over synonym matches
            label_pairs = [p for p in pairs if p[1] == "label"]
            if label_pairs:
                best = (f"unit_name_to_label", label_pairs[0][0])
            else:
                best = (f"unit_name_to_{pairs[0][1]}", pairs[0][0])
            for e, src in pairs:
                match_info["all_matches"].append({
                    "method": f"unit_name_to_{src}",
                    "uo_uri": e["uri"], "uo_id": e["id"], "uo_label": e["label"],
                })

        # --- Strategy 2: symbol -> UO symbol synonyms (case-sensitive) ---
        # Validate with plausibility check to reject coincidental symbol collisions
        if not best and symbol:
            sym_norm = normalize_symbol_for_match(symbol)
            if sym_norm and sym_norm in symbol_map:
                pairs = symbol_map[sym_norm]
                # Filter to plausible matches
                plausible = [
                    (e, src) for e, src in pairs
                    if symbol_match_is_plausible(unit_name, e)
                ]
                if plausible:
                    best = ("symbol_to_synonym", plausible[0][0])
                    for e, src in plausible:
                        match_info["all_matches"].append({
                            "method": f"symbol_to_{src}",
                            "uo_uri": e["uri"], "uo_id": e["id"], "uo_label": e["label"],
                        })

        # --- Strategy 3: plural -> UO names ---
        if not best and plural:
            norm_plural = normalize_name(plural)
            if norm_plural and norm_plural in name_map:
                pairs = name_map[norm_plural]
                best = ("plural_to_uo", pairs[0][0])
                for e, src in pairs:
                    match_info["all_matches"].append({
                        "method": f"plural_to_{src}",
                        "uo_uri": e["uri"], "uo_id": e["id"], "uo_label": e["label"],
                    })

        # --- Strategy 4: alternate_unit -> UO names ---
        if not best:
            for alt in alternates:
                norm_alt = normalize_name(alt)
                if norm_alt and norm_alt in name_map:
                    pairs = name_map[norm_alt]
                    best = ("alternate_unit_to_uo", pairs[0][0])
                    for e, src in pairs:
                        match_info["all_matches"].append({
                            "method": f"alternate_unit_to_{src}",
                            "uo_uri": e["uri"], "uo_id": e["id"], "uo_label": e["label"],
                            "alternate_unit": alt,
                        })
                    break

        # --- Strategy 5: canonical_unit -> UO names ---
        if not best and canonical:
            norm_canon = normalize_name(canonical)
            if norm_canon and norm_canon != norm_unit and norm_canon in name_map:
                pairs = name_map[norm_canon]
                best = ("canonical_unit_to_uo", pairs[0][0])
                for e, src in pairs:
                    match_info["all_matches"].append({
                        "method": f"canonical_unit_to_{src}",
                        "uo_uri": e["uri"], "uo_id": e["id"], "uo_label": e["label"],
                    })

        # --- Strategy 6: spelling variant of unit name ---
        if not best and norm_unit:
            result = try_spelling_variant_match(norm_unit, name_map)
            if result:
                entry, method, variant, pairs = result
                best = (f"spelling_variant", entry)
                for e, src in pairs:
                    match_info["all_matches"].append({
                        "method": f"spelling_variant_{src}",
                        "uo_uri": e["uri"], "uo_id": e["id"], "uo_label": e["label"],
                        "variant": variant,
                    })

        # --- Strategy 7: per-decomposition with spelling variants ---
        if not best and norm_unit:
            result = try_per_decomposition_match(norm_unit, name_map)
            if result:
                entry, method, variant, pairs = result
                best = ("per_variant", entry)
                for e, src in pairs:
                    match_info["all_matches"].append({
                        "method": method,
                        "uo_uri": e["uri"], "uo_id": e["id"], "uo_label": e["label"],
                        "variant": variant,
                    })

        # --- Strategy 8: square/cubic with spelling variants ---
        if not best and norm_unit:
            result = try_shape_variant_match(norm_unit, name_map)
            if result:
                entry, method, variant, pairs = result
                best = ("shape_variant", entry)
                for e, src in pairs:
                    match_info["all_matches"].append({
                        "method": method,
                        "uo_uri": e["uri"], "uo_id": e["id"], "uo_label": e["label"],
                        "variant": variant,
                    })

        # --- Strategy 9: alternate_unit spelling variants ---
        if not best:
            for alt in alternates:
                norm_alt = normalize_name(alt)
                if norm_alt:
                    result = try_spelling_variant_match(norm_alt, name_map)
                    if result:
                        entry, method, variant, pairs = result
                        best = ("alternate_spelling_variant", entry)
                        for e, src in pairs:
                            match_info["all_matches"].append({
                                "method": f"alternate_spelling_variant_{src}",
                                "uo_uri": e["uri"], "uo_id": e["id"], "uo_label": e["label"],
                                "alternate_unit": alt, "variant": variant,
                            })
                        break

        if best:
            method, entry = best
            match_info["matched"] = True
            match_info["match_method"] = method
            match_info["match_uo_uri"] = entry["uri"]
            match_info["match_uo_label"] = entry["label"]
            match_info["match_uo_id"] = entry["id"]
            matched_count += 1
            method_counts[method] += 1

        results.append(match_info)

    return results, matched_count, method_counts


# ===================================================================
# Part 4: Statistics and reporting
# ===================================================================

def compute_statistics(uo_entries, dataset, match_results, matched_count, method_counts):
    """Compute comprehensive statistics about the extraction and matching."""
    total_uo = len(uo_entries)
    deprecated = sum(1 for e in uo_entries if e["deprecated"])
    active_uo = total_uo - deprecated
    with_label = sum(1 for e in uo_entries if e.get("label") and not e["deprecated"])
    with_definition = sum(1 for e in uo_entries if e.get("definition") and not e["deprecated"])
    with_exact_syn = sum(1 for e in uo_entries if e.get("exact_synonyms") and not e["deprecated"])
    with_related_syn = sum(1 for e in uo_entries if e.get("related_synonyms") and not e["deprecated"])
    with_narrow_syn = sum(1 for e in uo_entries if e.get("narrow_synonyms") and not e["deprecated"])
    with_parents = sum(1 for e in uo_entries if e.get("parent_classes") and not e["deprecated"])

    total_exact_syns = sum(len(e.get("exact_synonyms", [])) for e in uo_entries if not e["deprecated"])
    total_related_syns = sum(len(e.get("related_synonyms", [])) for e in uo_entries if not e["deprecated"])
    total_narrow_syns = sum(len(e.get("narrow_synonyms", [])) for e in uo_entries if not e["deprecated"])

    total_dataset = len(dataset)

    # Categorize matches
    matched_entries = [r for r in match_results if r["matched"]]
    unmatched_entries = [r for r in match_results if not r["matched"]]

    # Which UO entries were matched?
    matched_uo_uris = set()
    for r in matched_entries:
        if r.get("match_uo_uri"):
            matched_uo_uris.add(r["match_uo_uri"])

    # Method breakdown
    method_breakdown = {}
    for method, count in sorted(method_counts.items(), key=lambda x: -x[1]):
        method_breakdown[method] = count

    # Build a fast lookup: (unit, symbol) -> dataset record
    dataset_lookup = {}
    for rec in dataset:
        key = (rec["unit"], rec.get("symbol", ""))
        dataset_lookup[key] = rec

    # System distribution
    matched_systems = Counter()
    unmatched_systems = Counter()
    matched_properties = Counter()
    unmatched_properties = Counter()

    for r in match_results:
        key = (r["unit"], r.get("symbol", ""))
        rec = dataset_lookup.get(key)
        if rec:
            system = rec.get("system", "unknown")
            prop = rec.get("property", "unknown")
            if r["matched"]:
                matched_systems[system] += 1
                matched_properties[prop] += 1
            else:
                unmatched_systems[system] += 1
                unmatched_properties[prop] += 1

    stats = {
        "uo_extraction": {
            "total_uo_entries": total_uo,
            "deprecated_entries": deprecated,
            "active_entries": active_uo,
            "with_label": with_label,
            "without_label": active_uo - with_label,
            "with_definition": with_definition,
            "with_exact_synonyms": with_exact_syn,
            "with_related_synonyms": with_related_syn,
            "with_narrow_synonyms": with_narrow_syn,
            "with_parent_classes": with_parents,
            "total_exact_synonyms": total_exact_syns,
            "total_related_synonyms": total_related_syns,
            "total_narrow_synonyms": total_narrow_syns,
        },
        "matching": {
            "total_dataset_entries": total_dataset,
            "matched_entries": matched_count,
            "unmatched_entries": total_dataset - matched_count,
            "match_rate_percent": round(100.0 * matched_count / total_dataset, 2) if total_dataset else 0,
            "unique_uo_entries_matched": len(matched_uo_uris),
            "method_breakdown": method_breakdown,
        },
        "system_distribution": {
            "matched_by_system": dict(matched_systems.most_common()),
            "unmatched_by_system": dict(unmatched_systems.most_common()),
        },
        "property_distribution": {
            "matched_by_property": dict(matched_properties.most_common(30)),
            "unmatched_by_property": dict(unmatched_properties.most_common(30)),
        },
    }

    return stats, matched_entries, unmatched_entries


def print_report(stats, matched_entries, unmatched_entries, uo_entries):
    """Print a human-readable report to stdout."""
    print("\n" + "=" * 80)
    print("UO OWL EXTRACTION AND MATCHING REPORT")
    print("=" * 80)

    uo = stats["uo_extraction"]
    print(f"\n--- UO Ontology Extraction ---")
    print(f"  Total UO entries parsed:      {uo['total_uo_entries']}")
    print(f"  Deprecated entries:            {uo['deprecated_entries']}")
    print(f"  Active (non-obsolete) entries: {uo['active_entries']}")
    print(f"  Entries with label:            {uo['with_label']}")
    print(f"  Entries without label:         {uo['without_label']}")
    print(f"  Entries with definition:       {uo['with_definition']}")
    print(f"  Entries with exact synonyms:   {uo['with_exact_synonyms']}")
    print(f"  Entries with related synonyms: {uo['with_related_synonyms']}")
    print(f"  Entries with narrow synonyms:  {uo['with_narrow_synonyms']}")
    print(f"  Entries with parent classes:   {uo['with_parent_classes']}")
    print(f"  Total exact synonyms:          {uo['total_exact_synonyms']}")
    print(f"  Total related synonyms:        {uo['total_related_synonyms']}")
    print(f"  Total narrow synonyms:         {uo['total_narrow_synonyms']}")

    m = stats["matching"]
    print(f"\n--- Dataset Matching ---")
    print(f"  Total dataset entries:  {m['total_dataset_entries']}")
    print(f"  Matched entries:        {m['matched_entries']}")
    print(f"  Unmatched entries:      {m['unmatched_entries']}")
    print(f"  Match rate:             {m['match_rate_percent']}%")
    print(f"  Unique UO entries used: {m['unique_uo_entries_matched']}")

    print(f"\n  Match method breakdown:")
    for method, count in sorted(m["method_breakdown"].items(), key=lambda x: -x[1]):
        print(f"    {method:40s} {count:5d}")

    sd = stats["system_distribution"]
    print(f"\n  Matched by measurement system:")
    for system, count in sorted(sd["matched_by_system"].items(), key=lambda x: -x[1]):
        print(f"    {system:20s} {count:5d}")
    print(f"\n  Unmatched by measurement system:")
    for system, count in sorted(sd["unmatched_by_system"].items(), key=lambda x: -x[1]):
        print(f"    {system:20s} {count:5d}")

    pd = stats["property_distribution"]
    print(f"\n  Top matched by physical property:")
    for prop, count in sorted(pd["matched_by_property"].items(), key=lambda x: -x[1])[:15]:
        print(f"    {prop:35s} {count:5d}")
    print(f"\n  Top unmatched by physical property:")
    for prop, count in sorted(pd["unmatched_by_property"].items(), key=lambda x: -x[1])[:15]:
        print(f"    {prop:35s} {count:5d}")

    # Sample matched entries
    print(f"\n--- Sample Matched Entries (first 30) ---")
    for r in matched_entries[:30]:
        uo_label = r.get("match_uo_label") or "?"
        print(f"  {r['unit']:40s} -> {uo_label:40s} [{r['match_method']}] ({r['match_uo_id']})")

    # Sample unmatched entries (diverse selection)
    print(f"\n--- Sample Unmatched Entries (first 40) ---")
    for r in unmatched_entries[:40]:
        print(f"  {r['unit']:50s} (symbol: {r.get('symbol', '')}, property: {r.get('property', '')})")

    # Show UO entries that have labels but were not matched by any dataset entry
    matched_uo_uris = set(r["match_uo_uri"] for r in matched_entries if r.get("match_uo_uri"))
    unmatched_uo = [
        e for e in uo_entries
        if not e["deprecated"] and e.get("label") and e["uri"] not in matched_uo_uris
    ]
    print(f"\n--- UO Entries Not Matched by Any Dataset Entry ({len(unmatched_uo)} total, showing first 40) ---")
    for e in unmatched_uo[:40]:
        syns = ", ".join(e.get("exact_synonyms", [])[:3])
        defn = (e.get("definition") or "")[:60]
        print(f"  {e['id']:15s} {e['label']:40s} [{syns}] {defn}")

    print("\n" + "=" * 80)


# ===================================================================
# Main
# ===================================================================

def main():
    # Validate files exist
    for path, desc in [(OWL_FILE, "UO OWL file"), (DATASET_FILE, "Dataset JSONL file")]:
        if not os.path.isfile(path):
            print(f"ERROR: {desc} not found: {path}", file=sys.stderr)
            sys.exit(1)

    # Step 1: Extract UO entries from OWL
    uo_entries = parse_uo_owl(OWL_FILE)
    print(f"Extracted {len(uo_entries)} UO entries from OWL file")

    # Save extracted UO data
    os.makedirs(os.path.dirname(EXTRACTED_OUT), exist_ok=True)
    with open(EXTRACTED_OUT, "w", encoding="utf-8") as f:
        json.dump(uo_entries, f, indent=2, ensure_ascii=False)
    print(f"Saved extracted UO data to: {EXTRACTED_OUT}")

    # Step 2: Load dataset
    dataset = load_dataset(DATASET_FILE)
    print(f"Loaded {len(dataset)} dataset entries")

    # Step 3: Match
    print("Running matching...")
    match_results, matched_count, method_counts = match_dataset(dataset, uo_entries)

    # Step 4: Statistics
    stats, matched_entries, unmatched_entries = compute_statistics(
        uo_entries, dataset, match_results, matched_count, method_counts
    )

    # Step 5: Save match results
    output = {
        "statistics": stats,
        "matches": [r for r in match_results if r["matched"]],
        "unmatched": [
            {
                "unit": r["unit"],
                "symbol": r.get("symbol", ""),
                "property": r.get("property", ""),
                "quantity": r.get("quantity", ""),
                "system": r.get("system", ""),
            }
            for r in match_results if not r["matched"]
        ],
    }

    with open(MATCHES_OUT, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Saved match results to: {MATCHES_OUT}")

    # Step 6: Print report
    print_report(stats, matched_entries, unmatched_entries, uo_entries)


if __name__ == "__main__":
    main()
