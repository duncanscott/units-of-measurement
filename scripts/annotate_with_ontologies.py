"""Annotate units with OM/UO/UCUM identifiers without touching the source dataset."""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional


OM_BASE = "http://www.ontology-of-units-of-measure.org/resource/om-2/"
RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS_NS = "http://www.w3.org/2000/01/rdf-schema#"
XML_NS = "http://www.w3.org/XML/1998/namespace"


@dataclass
class UOTerm:
    uri: str
    label: str
    definition: Optional[str]
    label_norm: Optional[str]
    definition_norm: Optional[str]

    @property
    def curie(self) -> str:
        return self.uri.rsplit("/", 1)[-1].replace("_", ":")


@dataclass
class OMTerm:
    uri: str
    label: str
    definition: Optional[str]
    quantities: List[str]
    dimension: Optional[str] = None
    label_norm: Optional[str] = None


def normalize_name(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    text = unicodedata.normalize("NFKC", text.lower())
    replacements = {
        "+": " plus ",
        "·": " ",
        "⋅": " ",
        "×": " x ",
        "^": "",
        "²": "2",
        "³": "3",
        "⁻": "-",
        "–": "-",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    text = text.replace("-", " ").replace("_", " ")
    text = re.sub(r"[^a-z0-9\s/·\.]", "", text)
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    if not text:
        return None
    replacements = {
        "metre": "meter",
        "centimetre": "centimeter",
        "millimetre": "millimeter",
        "kilometre": "kilometer",
        "litre": "liter",
        "metres": "meters",
        "litres": "liters",
        "gramme": "gram",
        "grammes": "grams",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text or None


def normalize_ucum(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    text = unicodedata.normalize("NFKC", text)
    replacements = {
        "·": ".",
        "⋅": ".",
        "×": ".",
        " " : "",
        "″": "''",
        "′": "'",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    text = text.replace("/", "/").replace("\\", "/")
    return text


def load_jsonl(path: Path) -> List[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_uo_terms(path: Path) -> Dict[str, List[UOTerm]]:
    name_map: Dict[str, List[UOTerm]] = defaultdict(list)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            uri = row.get("Class ID")
            label = row.get("Preferred Label") or ""
            if not uri:
                continue
            definition = row.get("Definitions") or None
            term = UOTerm(
                uri=uri,
                label=label,
                definition=definition,
                label_norm=normalize_name(label),
                definition_norm=normalize_name(definition),
            )
            names: List[str] = [label]
            for key in ("Synonyms", "has_exact_synonym", "has_related_synonym"):
                raw = row.get(key)
                if raw:
                    names.extend(x.strip() for x in raw.split("|") if x.strip())
            seen: set[str] = set()
            for name in names:
                norm = normalize_name(name)
                if not norm or norm in seen:
                    continue
                seen.add(norm)
                name_map[norm].append(term)
    return name_map


def load_ucum_codes(path: Path) -> tuple[Dict[str, List[Dict[str, str]]], Dict[str, List[Dict[str, str]]]]:
    code_map: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    uri_map: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    current: Optional[str] = None
    with path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            if line == ".":
                current = None
                continue
            if line.startswith("om:"):
                current = line.split()[0][3:]
                continue
            if current and line.startswith("skos:notation"):
                start = line.find("\"")
                end = line.find("\"", start + 1)
                if start == -1 or end == -1:
                    continue
                code = line[start + 1 : end]
                normalized = normalize_ucum(code)
                if not normalized:
                    continue
                entry = {
                    "code": code,
                    "normalized": normalized,
                    "uri": f"{OM_BASE}{current}",
                }
                code_map[normalized].append(entry)
                uri_map[entry["uri"]].append(entry)
    return code_map, uri_map


def find_unique(entries: List) -> Optional:
    if len(entries) == 1:
        return entries[0]
    return None


def select_best_uo(record: dict, matches: List[UOTerm], norm_names: List[Optional[str]]) -> Optional[UOTerm]:
    if not matches:
        return None
    prop = normalize_name(record.get("property"))
    quantity = normalize_name(record.get("quantity"))
    name_set = {name for name in norm_names if name}
    if len(matches) == 1:
        term = matches[0]
        if (not prop and not quantity) or _uo_matches_context(term, prop, quantity):
            return term
        return None
    best: Optional[UOTerm] = None
    best_score = 0
    for term in matches:
        score = 0
        if term.label_norm and term.label_norm in name_set:
            score += 4
        if prop:
            if term.label_norm and prop in term.label_norm:
                score += 3
            if term.definition_norm and prop in term.definition_norm:
                score += 2
        if quantity and quantity != prop:
            if term.label_norm and quantity in term.label_norm:
                score += 2
            if term.definition_norm and quantity in term.definition_norm:
                score += 1
        if score > best_score:
            best = term
            best_score = score
    if best_score > 0:
        if (not prop and not quantity) or _uo_matches_context(best, prop, quantity):
            return best
    return None


def _uo_matches_context(term: UOTerm, prop: Optional[str], quantity: Optional[str]) -> bool:
    if prop:
        if term.label_norm and prop in term.label_norm:
            return True
        if term.definition_norm and prop in term.definition_norm:
            return True
    if quantity:
        if term.label_norm and quantity in term.label_norm:
            return True
        if term.definition_norm and quantity in term.definition_norm:
            return True
    return False


def load_om_terms(path: Path) -> tuple[Dict[str, List[OMTerm]], Dict[str, OMTerm]]:
    tree = ET.parse(path)
    root = tree.getroot()
    ns = {"rdf": RDF_NS, "rdfs": RDFS_NS, "om": OM_BASE}
    # Build a map of uri -> label for quantity/dimension nodes
    label_map: Dict[str, str] = {}
    for elem in root.iter():
        uri = elem.attrib.get(f"{{{RDF_NS}}}about")
        if not uri:
            continue
        label_text = None
        for lbl in elem.findall("rdfs:label", ns):
            lang = lbl.attrib.get(f"{{{XML_NS}}}lang") or "en"
            if lang.lower() != "en":
                continue
            if lbl.text:
                label_text = lbl.text
                break
        if label_text:
            label_map[uri] = label_text

    name_map: Dict[str, List[OMTerm]] = defaultdict(list)
    uri_map: Dict[str, OMTerm] = {}
    unit_markers = (
        "om:symbol",
        "om:hasDimension",
        "om:hasUnit",
        "om:hasPrefix",
        "om:hasNumerator",
        "om:hasDenominator",
        "om:hasFactor",
    )

    for elem in root.iter():
        uri = elem.attrib.get(f"{{{RDF_NS}}}about")
        if not uri or not uri.startswith(OM_BASE):
            continue
        local_tag = elem.tag.split("}", 1)[-1]
        if local_tag.endswith("Quantity") or local_tag.endswith("Dimension"):
            continue
        is_unit_like = any(elem.find(marker, ns) is not None for marker in unit_markers)
        if not is_unit_like:
            continue

        labels = []
        for lbl in elem.findall("rdfs:label", ns):
            lang = lbl.attrib.get(f"{{{XML_NS}}}lang") or "en"
            if lang.lower() != "en" or not lbl.text:
                continue
            labels.append(lbl.text)
        if not labels:
            continue

        alternative_labels = [node.text for node in elem.findall("om:alternativeLabel", ns) if node.text]
        comments = [node.text for node in elem.findall("rdfs:comment", ns) if node.text]
        definition = comments[0] if comments else None

        quantities: List[str] = []
        for rel in elem.findall("om:hasQuantity", ns):
            ref = rel.attrib.get(f"{{{RDF_NS}}}resource")
            if not ref:
                continue
            q_label = label_map.get(ref)
            norm = normalize_name(q_label)
            if norm:
                quantities.append(norm)

        dimension = None
        dim = elem.find("om:hasDimension", ns)
        if dim is not None:
            ref = dim.attrib.get(f"{{{RDF_NS}}}resource")
            if ref:
                dimension = label_map.get(ref)

        term = OMTerm(
            uri=uri,
            label=labels[0],
            definition=definition,
            quantities=quantities,
            dimension=dimension,
            label_norm=normalize_name(labels[0]),
        )
        uri_map[uri] = term

        names: List[str] = labels + alternative_labels
        for sym_tag in ("om:symbol", "om:alternativeSymbol", "om:LaTeXSymbol"):
            for node in elem.findall(sym_tag, ns):
                if node.text:
                    names.append(node.text)
        names.append(uri.rsplit("/", 1)[-1])

        seen: set[str] = set()
        for name in names:
            norm = normalize_name(name)
            if not norm or norm in seen:
                continue
            seen.add(norm)
            name_map[norm].append(term)
    return name_map, uri_map


def select_ucum_entry(record: dict, entries: List[Dict[str, str]]) -> Optional[Dict[str, str]]:
    if not entries:
        return None
    if len(entries) == 1:
        return entries[0]
    candidate_names = [record.get("unit"), record.get("canonical_unit")]
    candidate_names.extend(record.get("alternate_unit", []) or [])
    normalized_targets = {norm for norm in (normalize_name(n) for n in candidate_names) if norm}
    for entry in entries:
        tail = entry["uri"].rsplit("/", 1)[-1]
        norm_tail = normalize_name(tail)
        if norm_tail and norm_tail in normalized_targets:
            return entry
    return None


def select_best_om(record: dict, entries: List[OMTerm], norm_names: List[Optional[str]]) -> Optional[OMTerm]:
    if not entries:
        return None
    name_set = {name for name in norm_names if name}
    if len(entries) == 1:
        entry = entries[0]
        if entry.label_norm and entry.label_norm in name_set:
            return entry
        return entry
    prop = normalize_name(record.get("property"))
    if prop:
        for entry in entries:
            if prop in entry.quantities:
                return entry
    quantity = normalize_name(record.get("quantity"))
    if quantity:
        for entry in entries:
            if quantity in entry.quantities:
                return entry
    if name_set:
        for entry in entries:
            if entry.label_norm and entry.label_norm in name_set:
                return entry
    return entries[0]


def annotate(
    records: List[dict],
    uo_map: Dict[str, List[UOTerm]],
    ucum_map: Dict[str, List[Dict[str, str]]],
    ucum_uri_map: Dict[str, List[Dict[str, str]]],
    om_name_map: Dict[str, List[OMTerm]],
    om_uri_map: Dict[str, OMTerm],
) -> tuple[List[dict], dict]:
    stats = {"total": len(records), "uo_matches": 0, "ucum_matches": 0, "om_matches": 0}
    enriched: List[dict] = []
    for record in records:
        augmented = dict(record)
        augmented.pop("external_ids", None)
        augmented.pop("ontology_metadata", None)
        names: List[str] = [record.get("unit"), record.get("canonical_unit")]
        names.extend(record.get("alternate_unit", []) or [])
        if record.get("symbol"):
            names.append(record["symbol"])
        norm_candidates = [normalize_name(name) for name in names if name]
        uo_term: Optional[UOTerm] = None
        for norm in norm_candidates:
            if not norm:
                continue
            matches = uo_map.get(norm)
            candidate = select_best_uo(record, matches or [], norm_candidates)
            if candidate:
                uo_term = candidate
                stats["uo_matches"] += 1
                break

        ucum_key = normalize_ucum(record.get("symbol"))
        ucum_entry = None
        if ucum_key:
            ucum_entry = select_ucum_entry(record, ucum_map.get(ucum_key) or [])
            if ucum_entry:
                stats["ucum_matches"] += 1

        om_entry = None
        if ucum_entry:
            om_entry = om_uri_map.get(ucum_entry["uri"])
        if not om_entry:
            om_candidates = []
            for norm in norm_candidates:
                if not norm:
                    continue
                om_candidates.extend(om_name_map.get(norm, []))
            om_entry = select_best_om(record, om_candidates, norm_candidates)
            if not ucum_entry and om_entry:
                ucum_options = ucum_uri_map.get(om_entry.uri)
                ucum_entry = find_unique(ucum_options or [])
                if ucum_entry:
                    stats["ucum_matches"] += 1
        if om_entry:
            stats["om_matches"] += 1

        external_ids = {}
        annotations = {}
        if uo_term:
            external_ids["uo"] = uo_term.curie
            annotations["uo"] = {"label": uo_term.label, "definition": uo_term.definition}
        if ucum_entry:
            external_ids["ucum"] = ucum_entry["code"]
        if om_entry:
            annotations.setdefault("om", {})
            annotations["om"].update({
                "uri": om_entry.uri,
                "label": om_entry.label,
                "definition": om_entry.definition,
            })
            if om_entry.quantities:
                annotations["om"]["quantities"] = om_entry.quantities
            if "ucum" in external_ids:
                annotations["om"]["ucum_code"] = external_ids["ucum"]

        if external_ids:
            augmented["external_ids"] = external_ids
        if annotations:
            augmented["ontology_metadata"] = annotations
        enriched.append(augmented)
    return enriched, stats


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Annotate units with ontology identifiers.")
    parser.add_argument("--units", default="jsonl/units_of_measurement.jsonl", help="Path to the units JSONL file")
    parser.add_argument("--uo", default="resource/bioportal/units_of_measure_ontology/UO.csv", help="Path to UO.csv")
    parser.add_argument("--om", default="resource/bioportal/units_of_measure_ontology/om-2.0.rdf", help="Path to om-2.0.rdf")
    parser.add_argument("--ucum", default="/Users/duncanscott/git-hub/HajoRijgersberg/OM/om-2-ucum.ttl", help="Path to om-2-ucum.ttl")
    parser.add_argument("--output", default="jsonl/units_with_ontologies.jsonl", help="Where to write the annotated JSONL")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    units_path = (root / args.units).resolve()
    uo_path = (root / args.uo).resolve()
    om_path = (root / args.om).resolve()
    ucum_path = Path(args.ucum).resolve()
    output_path = (root / args.output).resolve()

    records = load_jsonl(units_path)
    uo_map = load_uo_terms(uo_path)
    om_name_map, om_uri_map = load_om_terms(om_path)
    ucum_map, ucum_uri_map = load_ucum_codes(ucum_path)
    enriched, stats = annotate(records, uo_map, ucum_map, ucum_uri_map, om_name_map, om_uri_map)

    output_path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in enriched) + "\n", encoding="utf-8")
    print(f"Wrote {len(enriched)} records to {output_path}")
    print(
        "Matched {uo} units to UO, {ucum} to UCUM codes, and {om} to OM labels".format(
            uo=stats["uo_matches"], ucum=stats["ucum_matches"], om=stats["om_matches"]
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
