# Units of Measurement

A comprehensive collection of units of measurement covering 121 physical quantities and 11 measurement systems. Available in both JSON and JSONL formats.

## Files

The `jsonl/` directory contains three JSONL files (one JSON object per line). The `json/` directory contains the same datasets as JSON arrays.

### `units_of_measurement.jsonl`

The **comprehensive, merged dataset**. This is the file most users will want. It combines the SI and UOM datasets below into a single superset with a unified schema covering all fields.

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `unit` | string | Unit name (e.g., "kilometer", "pound") |
| `canonical_unit` | string | Canonical name using `·` and `/` delimiters (e.g., `watt/meter²·kelvin`) |
| `prefix` | string or null | SI prefix if applicable (e.g., "kilo", "milli") |
| `symbol` | string | Unit symbol (e.g., "km", "lb") |
| `plural` | string | Plural form (e.g., "kilometers", "pounds") |
| `property` | string | Physical quantity measured (e.g., "length", "mass") |
| `quantity` | string | Canonicalized physical quantity label (mirrors `property`) |
| `dimension` | object | SI base-exponent map (e.g., `{"L": 1, "T": -1}` for velocity); `{}` for dimensionless quantities |
| `conversion_factor` | number | Multiplier to convert to the reference unit |
| `conversion_offset` | number | Additive offset for temperature conversions (present only for Celsius and Fahrenheit) |
| `reference_unit` | string | The SI coherent unit that `conversion_factor` is relative to |
| `alternate_unit` | array of strings | Alternate names for the unit (present only where applicable, e.g., "metre" for "meter") |
| `system` | string | Measurement system (see below) |

The combination of `unit` and `property` is unique across all entries.

### `si_units.jsonl`

SI base units, SI derived units with special names, and non-SI units accepted for use with the SI (per the [SI Brochure, 9th Edition](https://www.bipm.org/en/publications/si-brochure)). Each unit includes full SI prefix expansions (all 24 prefixes from quecto through quetta). Uses US English spellings ("meter", "liter").

**Fields:** `unit`, `prefix`, `symbol`, `property`, `alternate_unit` (optional), `system`

### `uom.jsonl`

Units parsed from the Rust [uom](https://github.com/iliekturtles/uom) crate by Mike Boutin. Covers 117 physical quantities across multiple measurement systems, with conversion factors relative to the SI coherent unit for each quantity.

**Fields:** `unit`, `symbol`, `plural`, `property`, `conversion_factor`, `conversion_offset` (optional), `reference_unit`, `system`

## Measurement Systems

| System | Description |
|--------|-------------|
| SI | International System of Units |
| Metric | Metric units not part of SI (e.g., bar, calorie, liter, tonne) |
| Imperial | British Imperial units (e.g., foot, pound, gallon) |
| CGS | Centimetre-Gram-Second system (e.g., dyne, erg) |
| Nautical | Nautical units (nautical mile, knot) |
| Astronomical | Astronomical units (astronomical unit, light year, parsec) |
| Atomic/Natural | Atomic and natural units (Bohr radius, hartree) |
| IEC | IEC binary prefixes for information (kibibyte, mebibyte, etc.) |
| Information | Information units (bit, byte, shannon, nat) |
| Ancient Roman | Historical Roman units of length, mass, area, and volume |
| other | Units not clearly belonging to a single system |

## Conversion Factors

Each entry's `conversion_factor` is the multiplier to convert one unit to the `reference_unit` for that property. For example:

- **kilometer**: `conversion_factor: 1000.0`, `reference_unit: "meter"` -- 1 km = 1000 m
- **liter**: `conversion_factor: 0.001`, `reference_unit: "cubic meter"` -- 1 L = 0.001 m^3
- **pound**: `conversion_factor: 0.4535924`, `reference_unit: "kilogram"` -- 1 lb = 0.4536 kg

For temperature units with a `conversion_offset`, the conversion to the reference unit (kelvin) is: `value_in_kelvin = value * conversion_factor + conversion_offset`.

## Dimension

The `dimension` field encodes each unit's SI base-quantity exponents as an object. The keys correspond to the seven SI base quantities:

| Key | Base Quantity |
|-----|---------------|
| `L` | length |
| `M` | mass |
| `T` | time |
| `I` | electric current |
| `Θ` | thermodynamic temperature |
| `N` | amount of substance |
| `J` | luminous intensity |

Only non-zero exponents are included. For example, velocity (m/s) is `{"L": 1, "T": -1}` and power (W = kg·m²/s³) is `{"M": 1, "L": 2, "T": -3}`.

Dimensionless quantities — angle, solid angle, ratio, logarithmic ratio, and information — have an empty object `{}`. This follows SI convention: the radian and steradian are dimensionless derived units (dimension 1), and information units (bit, byte) fall outside the SI dimensional framework.

## Usage

### Install

```sh
npm install units-of-measurement   # Node.js
pip install units-of-measurement   # Python
```

### Python

```python
from units_of_measurement import load

units = load()  # all entries from the merged dataset

# Find all length units
length_units = [u for u in units if u["property"] == "length"]

# Convert 5 miles to meters
mile = next(u for u in units if u["unit"] == "mile")
meters = 5 * mile["conversion_factor"]  # 8046.72

# Canonical name & dimension vector for an acceleration unit
accel = next(u for u in units if u["unit"] == "meter per second squared")
accel["canonical_unit"]  # 'meter/second²'
accel["dimension"]       # {'L': 1, 'T': -2}
accel["quantity"] == accel["property"]  # True

# List all measurement systems
systems = sorted(set(u["system"] for u in units))

# Load a specific dataset
si = load("si_units")   # SI entries
uom = load("uom")       # uom entries
```

### JavaScript

```js
const { load } = require('units-of-measurement');
// or: import { load } from 'units-of-measurement';

const units = load(); // all entries from the merged dataset

// Find all mass units
const massUnits = units.filter(u => u.property === 'mass');

// Convert 10 pounds to kilograms
const pound = units.find(u => u.unit === 'pound' && u.property === 'mass');
const kg = 10 * pound.conversion_factor; // 4.535924

// Canonical representation + dimension vector
const accel = units.find(u => u.unit === 'meter per second squared');
console.log(accel.canonical_unit); // 'meter/second²'
console.log(accel.dimension);      // { L: 1, T: -2 }
console.log(accel.quantity === accel.property); // true

// Load a specific dataset
const si = load('si_units');
const uom = load('uom');
```

### Raw Data (no package needed)

```sh
# Download as JSON array
curl -LO https://raw.githubusercontent.com/duncanscott/units-of-measurement/main/json/units_of_measurement.json

# Download as JSONL
curl -LO https://raw.githubusercontent.com/duncanscott/units-of-measurement/main/jsonl/units_of_measurement.jsonl

# Query JSON with jq — all Imperial length units
jq -c '.[] | select(.property == "length" and .system == "Imperial")' json/units_of_measurement.json

# Query JSONL with jq
jq -c 'select(.property == "length" and .system == "Imperial")' jsonl/units_of_measurement.jsonl

### Focused Lists

`jsonl/units_of_measurement.jsonl` is the single source of truth, but you can build smaller slices directly from it by running:

```sh
python3 scripts/generate_focused_lists.py
```

This script reads the canonical JSONL and filters it into `jsonl/focused/`:

- `si_base_units.jsonl` keeps the eight SI base (and interval) units by checking the existing `property`/`unit` fields (e.g., `(length, meter)`).
- `property_summary.jsonl` aggregates counts per `property`, listing the observed `system` and `reference_unit` values and tallying how many entries already have `external_ids`.
- `biomedical_units.jsonl` includes any record that already carries a UO CURIE or a UCUM+OM pairing; no separate metadata files are required because it reuses `external_ids` and `ontology_metadata`.
- `uo_units.jsonl` lists every unit with a Unit Ontology identifier (pulled from `external_ids.uo`), along with the stored UO label/definition.
- `ucum_units.jsonl` lists every unit with a UCUM code (from `external_ids.ucum`) and includes the associated OM metadata so you can track the UCUM source.

Because each subset is derived purely from the fields in the canonical JSONL, re-running the script after any data change keeps the focused lists in sync without maintaining additional sources.
```

## Data Sources

- **[SI Brochure](https://www.bipm.org/en/publications/si-brochure)** (9th Edition, 2019) -- Bureau International des Poids et Mesures (BIPM). Source for SI base units, derived units, and non-SI units accepted for use with the SI.
- **[uom](https://github.com/iliekturtles/uom)** -- Units of Measurement Rust crate by Mike Boutin, licensed under MIT / Apache-2.0. Source for conversion factors, plurals, and extended unit coverage across multiple measurement systems. See [THIRD-PARTY-LICENSES](THIRD-PARTY-LICENSES) for the full license text.

## Acknowledgments

This project was built with assistance from [Claude](https://claude.ai) (Anthropic) and [Codex](https://openai.com/codex) (OpenAI).

## License

This project is licensed under the [MIT License](LICENSE).
