# Units of Measurement

A comprehensive collection of units of measurement in JSONL format, covering 121 physical quantities and 11 measurement systems.

## Files

The `json/` directory contains three JSONL files (one JSON object per line):

### `units_of_measurement.jsonl` (2,959 entries)

The **comprehensive, merged dataset**. This is the file most users will want. It combines the SI and UOM datasets below into a single superset with a unified schema covering all fields.

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `unit` | string | Unit name (e.g., "kilometer", "pound") |
| `prefix` | string or null | SI prefix if applicable (e.g., "kilo", "milli") |
| `symbol` | string | Unit symbol (e.g., "km", "lb") |
| `plural` | string | Plural form (e.g., "kilometers", "pounds") |
| `property` | string | Physical quantity measured (e.g., "length", "mass") |
| `conversion_factor` | number | Multiplier to convert to the reference unit |
| `conversion_offset` | number | Additive offset for temperature conversions (present only for Celsius and Fahrenheit) |
| `reference_unit` | string | The SI coherent unit that `conversion_factor` is relative to |
| `alternate_unit` | array of strings | Alternate names for the unit (present only where applicable, e.g., "metre" for "meter") |
| `system` | string | Measurement system (see below) |

### `si_units.jsonl` (812 entries)

SI base units, SI derived units with special names, and non-SI units accepted for use with the SI (per the [SI Brochure, 9th Edition](https://www.bipm.org/en/publications/si-brochure)). Each unit includes full SI prefix expansions (all 24 prefixes from quecto through quetta). Uses US English spellings ("meter", "liter").

**Fields:** `unit`, `prefix`, `symbol`, `property`, `alternate_unit` (optional), `system`

### `uom.jsonl` (2,660 entries)

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

## Usage

### Install

```sh
npm install units-of-measurement   # Node.js
pip install units-of-measurement   # Python
```

### Python

```python
from units_of_measurement import load

units = load()  # 2,959 entries from the merged dataset

# Find all length units
length_units = [u for u in units if u["property"] == "length"]

# Convert 5 miles to meters
mile = next(u for u in units if u["unit"] == "mile")
meters = 5 * mile["conversion_factor"]  # 8046.72

# List all measurement systems
systems = sorted(set(u["system"] for u in units))

# Load a specific dataset
si = load("si_units")   # 812 SI entries
uom = load("uom")       # 2,660 uom entries
```

### JavaScript

```js
const { load } = require('units-of-measurement');
// or: import { load } from 'units-of-measurement';

const units = load(); // 2,959 entries from the merged dataset

// Find all mass units
const massUnits = units.filter(u => u.property === 'mass');

// Convert 10 pounds to kilograms
const pound = units.find(u => u.unit === 'pound' && u.property === 'mass');
const kg = 10 * pound.conversion_factor; // 4.535924

// Load a specific dataset
const si = load('si_units');
const uom = load('uom');
```

### Raw JSONL (no package needed)

```sh
# Download the dataset directly
curl -LO https://raw.githubusercontent.com/duncanscott/units-of-measurement/main/json/units_of_measurement.jsonl

# Query with jq — all Imperial length units
jq -c 'select(.property == "length" and .system == "Imperial")' json/units_of_measurement.jsonl
```

## Data Sources

- **SI Brochure** (9th Edition, 2019) -- Bureau International des Poids et Mesures (BIPM). Source for SI base units, derived units, and non-SI units accepted for use with the SI.
- **[uom](https://github.com/iliekturtles/uom)** -- Units of Measurement Rust crate by Mike Boutin, licensed under MIT / Apache-2.0. Source for conversion factors, plurals, and extended unit coverage across multiple measurement systems. See [THIRD-PARTY-LICENSES](THIRD-PARTY-LICENSES) for the full license text.

## License

This project is licensed under the [MIT License](LICENSE).
