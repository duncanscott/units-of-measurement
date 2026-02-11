# Ontology Resource Notes

## Local Resource Inventory
- **BioPortal exports** (`resource/bioportal/units_of_measure_ontology/`): contains `OM.csv`, `om-2.0.rdf`, `UO.csv`, `uo.owl`, `owlapi.xrdf`, and a Bubastis diff. `OM.csv` primarily enumerates quantity and phenomenon classes with pointers to the OM unit IRIs (e.g., `http://www.ontology-of-units-of-measure.org/resource/om-2/metre`). `UO.csv` lists each Unit Ontology class with its IRI (`Class ID`), synonyms, textual definitions, and parentage columns such as `is_unit_of`.
- **OM GitHub clone** (`/Users/duncanscott/git-hub/HajoRijgersberg/OM`): ships the authoritative `om-2.0.rdf` plus auxiliary Turtle files. `om-2-ucum.ttl` maps every OM unit (`om:metre`, `om:kelvin`, …) to UCUM codes via `skos:notation`, which is the cleanest place to extract universal identifiers.
- **Unit Ontology GitHub clone** (`/Users/duncanscott/git-hub/bio-ontology-research-group/unit-ontology`): includes the maintained `uo.owl`, `uo.obo`, JSON serializations, and the ODK editing stack under `src/ontology/uo-edit.owl`. Provides stable CURIEs (`UO:0000008`) and definitions for most scientific units.
- **Portals**: https://bioportal.bioontology.org/ontologies/ offers alternative ontologies (e.g., QUDT, PATO) if we need domain-specific vocabularies. https://ontobee.org/ontology/UO renders browsable term pages that expose cross-references not present in the CSV dumps.

## Applicability to `jsonl/units_of_measurement.jsonl`
- OM and UO both supply globally unique IRIs plus definitions, so we can extend each unit record with an `external_ids` object: `{ "om": ".../metre", "uo": "UO:0000008", "ucum": "m" }`.
- `om-2-ucum.ttl` gives canonical UCUM strings (e.g., `"m"`, `"K"`, `"cd"`). These codes fill the “universal identifier” requirement and align with the healthcare and laboratory datasets you downloaded from BioPortal.
- `UO.csv`’s `Synonyms` and `has_exact_synonym` columns can populate a richer `alternate_unit` array and tie back to biomedical naming conventions (e.g., `kilogram per metre` vs. `kg/m`).
- `OM.csv` focuses on physical quantities (`Length`, `ElectricCurrent`) and their admissible units. That suggests splitting our data into a `quantities.jsonl` (one line per property with definitions, symbols, OM links) plus `units.jsonl` (current file) to mimic OM’s separation of quantities and units.

## Fields & Lists Worth Adding
- **New fields** inside `jsonl/units_of_measurement.jsonl`: `definition` (source + text), `external_ids` (OM/UO/UCUM/Wikidata), `source_url`, `scale` (for Celsius vs. kelvin as encouraged by OM), and optionally `unit_class` (base, derived, scale, financial, etc.).
- **New artifact** created now: `jsonl/ontology_crosswalk_base_units.jsonl` aligns the seven SI base units with OM IRIs, Unit Ontology CURIEs, and UCUM codes extracted from `om-2-ucum.ttl` plus `UO.csv`. Use it as the seed for a broader crosswalk generator.
- **Potential future lists**: `jsonl/quantities.jsonl` sourced from `OM.csv`, `jsonl/scales.jsonl` describing absolute vs. relative scales, and `jsonl/ontology_sources.jsonl` cataloging which upstream ontology each measurement system pulls from.

## Suggested Next Steps
1. Write a small ETL that reads `UO.csv` and `om-2-ucum.ttl`, joins on labels/UCUM codes, and annotates every entry in `jsonl/units_of_measurement.jsonl` with those identifiers (while keeping the original file unmodified until reviewed).
2. Parse `om-2.0.rdf` (via `rdflib` or `owlready2`) to extract unit definitions and relationships (e.g., `om:hasBaseUnit`, `om:hasDimension`) so we can verify or enrich our `dimension` vectors programmatically.
3. Consider publishing multiple derivative lists: one for SI-only units, one for biomedical-specific UO units, and one for ontology crosswalks—mirroring the multiple downloads you placed under `resource/bioportal/`.
