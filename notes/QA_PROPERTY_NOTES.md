# QA Property Synonyms

- Added the small synonym map inside `scripts/validate_ontology_annotations.py` so the QA script treats phrases like `activity (of a radionuclide)` as valid hits for the `radioactivity` property, and `gram per milliliter` as a stand-in for `mass concentration`.
- If additional mismatches appear, extend the `property_synonyms` dict rather than hardcoding suppressions. Keep the list short and focused on ontology vocabulary gaps.
