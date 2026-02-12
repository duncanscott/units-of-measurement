"""Add ~70 new units from the OM ontology to the canonical dataset.

Each unit record includes ontology_metadata.om sourced from the OM RDF.
Records are appended to the existing JSONL and re-sorted by property.
"""

from __future__ import annotations

import json
from pathlib import Path

OM_BASE = "http://www.ontology-of-units-of-measure.org/resource/om-2/"


def om(local: str, label: str, definition: str | None) -> dict:
    """Build ontology_metadata.om dict."""
    return {"om": {"uri": f"{OM_BASE}{local}", "label": label, "definition": definition}}


def rec(
    unit: str,
    canonical_unit: str,
    prefix: str | None,
    symbol: str,
    plural: str,
    prop: str,
    dimension: dict,
    conversion_factor: float,
    reference_unit: str,
    system: str,
    om_local: str,
    om_label: str,
    om_definition: str | None,
    *,
    alternate_unit: list[str] | None = None,
    conversion_offset: float | None = None,
    external_ids: dict | None = None,
) -> dict:
    """Build a complete record dict."""
    r: dict = {
        "unit": unit,
        "canonical_unit": canonical_unit,
        "prefix": prefix,
        "symbol": symbol,
        "plural": plural,
        "property": prop,
        "quantity": prop,
        "dimension": dimension,
        "conversion_factor": conversion_factor,
        "reference_unit": reference_unit,
        "system": system,
    }
    if conversion_offset is not None:
        r["conversion_offset"] = conversion_offset
    if alternate_unit:
        r["alternate_unit"] = alternate_unit
    if external_ids:
        r["external_ids"] = external_ids
    r["ontology_metadata"] = om(om_local, om_label, om_definition)
    return r


# ──────────────────────────────────────────────────────────────────────────────
# TIER 1: Singular/base units (20 new)
# ──────────────────────────────────────────────────────────────────────────────

TIER_1 = [
    rec(
        "angstrom", "angstrom", None, "\u00c5", "angstroms",
        "length", {"L": 1}, 1e-10, "meter", "Metric",
        "angstrom", "angstrom",
        "The angstrom is a unit of length defined as 1.0e-10 metre.",
        alternate_unit=["\u00e5ngstr\u00f6m"],
        external_ids={"ucum": "Ao"},
    ),
    rec(
        "jansky", "jansky", None, "Jy", "janskys",
        "spectral flux density", {"M": 1, "T": -2}, 1e-26,
        "watt per square meter hertz", "Astronomical",
        "jansky", "jansky", None,
    ),
    rec(
        "barye", "barye", None, "ba", "baryes",
        "pressure", {"M": 1, "L": -1, "T": -2}, 0.1, "pascal", "CGS",
        "barye", "barye",
        "The barye is a unit of pressure defined as 0.1 pascal.",
    ),
    rec(
        "biot", "biot", None, "Bi", "biots",
        "electric current", {"I": 1}, 10.0, "ampere", "CGS",
        "biot", "biot",
        "The biot is a unit of electric current defined as 10 ampere.",
    ),
    rec(
        "rem", "rem", None, "rem", "rems",
        "dose equivalent", {"L": 2, "T": -2}, 0.01, "sievert", "CGS",
        "rem", "rem",
        "The rem is a unit of dose equivalent defined as 1.0e-2 sievert.",
        external_ids={"ucum": "REM"},
    ),
    rec(
        "darcy", "darcy", None, "D", "darcys",
        "permeability", {"L": 2}, 9.869233e-13, "square meter", "other",
        "darcy", "darcy",
        "The darcy is a unit of permeability defined as 9.869233e-13 square metre.",
    ),
    rec(
        "week", "week", None, "wk", "weeks",
        "time", {"T": 1}, 604800.0, "second", "other",
        "week", "week",
        "The week is a unit of time defined as 6.04800e5 second.",
        external_ids={"ucum": "wk"},
    ),
    rec(
        "month", "month", None, "mo", "months",
        "time", {"T": 1}, 2629800.0, "second", "other",
        "month", "month",
        "The month is a unit of time defined as 1/12 of a Julian year (365.25 days).",
        external_ids={"ucum": "mo"},
    ),
    rec(
        "British thermal unit (thermochemical)", "British\u00b7thermal\u00b7unit\u00b7(thermochemical)",
        None, "Btu_th", "British thermal units (thermochemical)",
        "energy", {"M": 1, "L": 2, "T": -2}, 1054.35, "joule", "Imperial",
        "BritishThermalUnit-Thermochemical", "British thermal unit (thermochemical)", None,
        external_ids={"ucum": "[Btu_th]"},
    ),
    rec(
        "calorie (thermochemical)", "calorie\u00b7(thermochemical)",
        None, "cal_th", "calories (thermochemical)",
        "energy", {"M": 1, "L": 2, "T": -2}, 4.184, "joule", "Metric",
        "calorie-Thermochemical", "calorie (thermochemical)", None,
        external_ids={"ucum": "cal_th"},
    ),
    rec(
        "furlong", "furlong", None, "fur", "furlongs",
        "length", {"L": 1}, 201.168, "meter", "Imperial",
        "furlong-International", "furlong (international)",
        "The international furlong is a unit of length defined as 201.168 metre.",
        external_ids={"ucum": "[fur_us]"},
    ),
    rec(
        "pint (imperial)", "pint\u00b7(imperial)", None, "pt (imp)", "pints (imperial)",
        "volume", {"L": 3}, 5.6826125e-4, "cubic meter", "Imperial",
        "pint-Imperial", "pint (imperial)",
        "The imperial pint is a unit of volume defined as 568.26125 millilitre.",
        external_ids={"ucum": "[pt_br]"},
    ),
    rec(
        "quart (imperial)", "quart\u00b7(imperial)", None, "qt (imp)", "quarts (imperial)",
        "volume", {"L": 3}, 1.1365225e-3, "cubic meter", "Imperial",
        "quart-Imperial", "quart (imperial)",
        "The imperial quart is a unit of volume defined as 1.1365225 litre.",
        external_ids={"ucum": "[qt_br]"},
    ),
    rec(
        "dessertspoon", "dessertspoon", None, "dsp", "dessertspoons",
        "volume", {"L": 3}, 1e-5, "cubic meter", "Imperial",
        "dessertspoon", "dessertspoon",
        "The dessertspoon is a unit of volume defined as 2 teaspoons (10 millilitres).",
    ),
    rec(
        "kayser", "kayser", None, "K", "kaysers",
        "reciprocal length", {"L": -1}, 100.0, "reciprocal meter", "CGS",
        "kayser", "kayser",
        "The kayser is a unit of wavenumber defined as 100 reciprocal metre.",
    ),
    rec(
        "rhe", "rhe", None, "rhe", "rhes",
        "fluidity", {"M": -1, "L": 1, "T": 1}, 10.0,
        "reciprocal pascal second", "CGS",
        "rhe", "rhe",
        "The rhe is a unit of fluidity defined as 10 reciprocal pascal second.",
    ),
    rec(
        "meter of mercury", "meter\u00b7of\u00b7mercury", None, "m Hg", "meters of mercury",
        "pressure", {"M": 1, "L": -1, "T": -2}, 133322.0, "pascal", "other",
        "metreOfMercury", "metre of mercury",
        "The metre of mercury is a unit of pressure defined as 133322 pascal.",
        alternate_unit=["metre of mercury"],
    ),
    rec(
        "stattesla", "stattesla", None, "statT", "statteslas",
        "magnetic flux density", {"M": 1, "T": -2, "I": -1}, 2.9979e6, "tesla", "CGS",
        "stattesla", "stattesla",
        "The stattesla is a unit of magnetic flux density defined as 2.9979e6 tesla.",
    ),
    rec(
        "statweber", "statweber", None, "statWb", "statwebers",
        "magnetic flux", {"M": 1, "L": 2, "T": -2, "I": -1}, 2.9979e2, "weber", "CGS",
        "statweber", "statweber",
        "The statweber is a unit of magnetic flux defined as 2.9979e2 weber.",
    ),
    rec(
        "minute (sidereal)", "minute\u00b7(sidereal)", None, "min (sid)", "minutes (sidereal)",
        "time", {"T": 1}, 59.83617, "second", "Astronomical",
        "minute-Sidereal", "minute (sidereal)",
        "The sidereal minute is a unit of time defined as 5.983617e1 second.",
    ),
]


# ──────────────────────────────────────────────────────────────────────────────
# TIER 2: Quotient/derived units (28 new)
# ──────────────────────────────────────────────────────────────────────────────

TIER_2 = [
    rec(
        "coulomb per kilogram", "coulomb/kilogram", None, "C/kg",
        "coulombs per kilogram",
        "exposure", {"I": 1, "T": 1, "M": -1}, 1.0,
        "coulomb per kilogram", "SI",
        "coulombPerKilogram", "coulomb per kilogram", None,
        external_ids={"ucum": "C/kg"},
    ),
    rec(
        "gray per second", "gray/second", None, "Gy/s",
        "grays per second",
        "absorbed dose rate", {"L": 2, "T": -3}, 1.0,
        "gray per second", "SI",
        "grayPerSecond-Time", "gray per second", None,
        external_ids={"ucum": "Gy/s"},
    ),
    rec(
        "milligray per second", "milligray/second", "milli", "mGy/s",
        "milligrays per second",
        "absorbed dose rate", {"L": 2, "T": -3}, 0.001,
        "gray per second", "SI",
        "milligrayPerSecond-Time", "milligray per second", None,
    ),
    rec(
        "joule per cubic meter", "joule/meter\u00b3", None, "J/m\u00b3",
        "joules per cubic meter",
        "energy density", {"M": 1, "L": -1, "T": -2}, 1.0,
        "joule per cubic meter", "SI",
        "joulePerCubicmetre", "joule per cubic metre", None,
        external_ids={"ucum": "J/m3"},
    ),
    rec(
        "lumen per watt", "lumen/watt", None, "lm/W",
        "lumens per watt",
        "luminous efficacy", {"M": -1, "L": -2, "T": 3, "J": 1}, 1.0,
        "lumen per watt", "SI",
        "lumenPerWatt", "lumen per watt", None,
        external_ids={"ucum": "lm/W"},
    ),
    rec(
        "lumen per square meter", "lumen/meter\u00b2", None, "lm/m\u00b2",
        "lumens per square meter",
        "luminous emittance", {"L": -2, "J": 1}, 1.0,
        "lumen per square meter", "SI",
        "lumenPerSquareMetre", "lumen per square metre", None,
        external_ids={"ucum": "lm/m2"},
    ),
    rec(
        "watt per steradian", "watt/steradian", None, "W/sr",
        "watts per steradian",
        "radiant intensity", {"M": 1, "L": 2, "T": -3}, 1.0,
        "watt per steradian", "SI",
        "wattPerSteradian", "watt per steradian", None,
        external_ids={"ucum": "W/sr"},
    ),
    rec(
        "watt per hertz", "watt/hertz", None, "W/Hz",
        "watts per hertz",
        "spectral power", {"M": 1, "L": 2, "T": -2}, 1.0,
        "watt per hertz", "SI",
        "wattPerHertz", "watt per hertz", None,
    ),
    rec(
        "watt per nanometer", "watt/nanometer", None, "W/nm",
        "watts per nanometer",
        "spectral power", {"M": 1, "L": 1, "T": -3}, 1e9,
        "watt per meter", "SI",
        "wattPerNanometre", "watt per nanometre", None,
    ),
    rec(
        "watt per square meter steradian", "watt/meter\u00b2\u00b7steradian",
        None, "W/(m\u00b2\u00b7sr)",
        "watts per square meter steradian",
        "spectral radiance", {"M": 1, "T": -3}, 1.0,
        "watt per square meter steradian", "SI",
        "wattPerSquareMetreSteradian", "watt per square metre steradian", None,
        external_ids={"ucum": "W/m2/sr"},
    ),
    rec(
        "ampere per watt", "ampere/watt", None, "A/W",
        "amperes per watt",
        "responsivity", {"I": 1, "M": -1, "L": -2, "T": 3}, 1.0,
        "ampere per watt", "SI",
        "amperePerWatt", "ampere per watt", None,
        external_ids={"ucum": "A/W"},
    ),
    rec(
        "gram per kilogram", "gram/kilogram", None, "g/kg",
        "grams per kilogram",
        "mass fraction", {}, 0.001, "one", "SI",
        "gramPerKilogram", "gram per kilogram", None,
        external_ids={"ucum": "g/kg"},
    ),
    rec(
        "milligram per kilogram", "milligram/kilogram", None, "mg/kg",
        "milligrams per kilogram",
        "mass fraction", {}, 1e-6, "one", "SI",
        "milligramPerKilogram", "milligram per kilogram", None,
        external_ids={"ucum": "mg/kg"},
    ),
    rec(
        "kilogram per hectare", "kilogram/hectare", None, "kg/ha",
        "kilograms per hectare",
        "areal mass density", {"M": 1, "L": -2}, 1e-4,
        "kilogram per square meter", "Metric",
        "kilogramPerHectare", "kilogram per hectare", None,
        external_ids={"ucum": "kg/har"},
    ),
    rec(
        "tonne per hectare", "tonne/hectare", None, "t/ha",
        "tonnes per hectare",
        "areal mass density", {"M": 1, "L": -2}, 0.1,
        "kilogram per square meter", "Metric",
        "tonnePerHectare", "tonne per hectare", None,
    ),
    rec(
        "liter per 100 kilometer", "liter/100\u00b7kilometer", None, "L/100 km",
        "liters per 100 kilometer",
        "fuel consumption", {"L": 2}, 1e-8,
        "square meter", "Metric",
        "litrePer100Kilometre", "litre per 100 kilometre", None,
        alternate_unit=["litre per 100 kilometre"],
    ),
    rec(
        "liter per hour", "liter/hour", None, "L/h",
        "liters per hour",
        "volume rate", {"L": 3, "T": -1}, 2.777778e-7,
        "cubic meter per second", "Metric",
        "litrePerHour", "litre per hour", None,
        alternate_unit=["litre per hour"],
    ),
    rec(
        "liter per kilogram", "liter/kilogram", None, "L/kg",
        "liters per kilogram",
        "specific volume", {"M": -1, "L": 3}, 0.001,
        "cubic meter per kilogram", "Metric",
        "litrePerKilogram", "litre per kilogram",
        "Litre per kilogram is a unit of specific volume defined as litre divided by kilogram.",
        alternate_unit=["litre per kilogram"],
    ),
    rec(
        "liter per mole", "liter/mole", None, "L/mol",
        "liters per mole",
        "molar volume", {"L": 3, "N": -1}, 0.001,
        "cubic meter per mole", "SI",
        "litrePerMole", "litre per mole", None,
        alternate_unit=["litre per mole"],
    ),
    rec(
        "millimeter per day", "millimeter/day", None, "mm/d",
        "millimeters per day",
        "velocity", {"L": 1, "T": -1}, 1.1574074074074073e-8,
        "meter per second", "SI",
        "millimetrePerDay", "millimetre per day",
        "Millimetre per day is a unit of speed defined as millimetre divided by day.",
        alternate_unit=["millimetre per day"],
    ),
    rec(
        "millimeter per hour", "millimeter/hour", None, "mm/h",
        "millimeters per hour",
        "velocity", {"L": 1, "T": -1}, 2.777777777777778e-7,
        "meter per second", "SI",
        "millimetrePerHour", "millimetre per hour",
        "Millimetre per hour is a unit of speed defined as millimetre divided by hour.",
        alternate_unit=["millimetre per hour"],
    ),
    rec(
        "meter per day", "meter/day", None, "m/d",
        "meters per day",
        "velocity", {"L": 1, "T": -1}, 1.1574074074074073e-5,
        "meter per second", "SI",
        "metrePerDay", "metre per day",
        "Metre per day is a unit of speed defined as metre divided by day.",
        alternate_unit=["metre per day"],
    ),
    rec(
        "meter per minute", "meter/minute", None, "m/min",
        "meters per minute",
        "velocity", {"L": 1, "T": -1}, 0.016666666666666666,
        "meter per second", "SI",
        "metrePerMinute-Time", "metre per minute",
        "Metre per minute is a unit of speed defined as metre divided by minute.",
        alternate_unit=["metre per minute"],
        external_ids={"ucum": "m/min"},
    ),
    rec(
        "centimeter per day", "centimeter/day", None, "cm/d",
        "centimeters per day",
        "velocity", {"L": 1, "T": -1}, 1.1574074074074074e-7,
        "meter per second", "SI",
        "centimetrePerDay", "centimetre per day",
        "Centimetre per day is a unit of speed defined as centimetre divided by day.",
        alternate_unit=["centimetre per day"],
    ),
    rec(
        "degree Celsius per second", "degree\u00b7Celsius/second", None, "\u00b0C/s",
        "degrees Celsius per second",
        "temperature rate", {"\u0398": 1, "T": -1}, 1.0,
        "kelvin per second", "Metric",
        "degreeCelsiusPerSecond-Time", "degree Celsius per second", None,
    ),
    rec(
        "degree Celsius per minute", "degree\u00b7Celsius/minute", None, "\u00b0C/min",
        "degrees Celsius per minute",
        "temperature rate", {"\u0398": 1, "T": -1}, 0.016666666666666666,
        "kelvin per second", "Metric",
        "degreeCelsiusPerMinute-Time", "degree Celsius per minute", None,
    ),
    rec(
        "degree Celsius per hour", "degree\u00b7Celsius/hour", None, "\u00b0C/h",
        "degrees Celsius per hour",
        "temperature rate", {"\u0398": 1, "T": -1}, 0.0002777777777777778,
        "kelvin per second", "Metric",
        "degreeCelsiusPerHour", "degree Celsius per hour", None,
    ),
    rec(
        "nautical mile per hour", "nautical\u00b7mile/hour", None, "nmi/h",
        "nautical miles per hour",
        "velocity", {"L": 1, "T": -1}, 0.5144444444444445,
        "meter per second", "Nautical",
        "nauticalMile-InternationalPerHour", "nautical mile per hour",
        "Nautical mile per hour is a unit of speed defined as nautical mile divided by hour.",
        alternate_unit=["knot (international)"],
    ),
]


# ──────────────────────────────────────────────────────────────────────────────
# TIER 3: Reciprocal/exponentiated units (7 new)
# ──────────────────────────────────────────────────────────────────────────────

TIER_3 = [
    rec(
        "reciprocal second", "reciprocal\u00b7second", None, "s\u207b\u00b9",
        "reciprocal seconds",
        "frequency", {"T": -1}, 1.0, "hertz", "SI",
        "reciprocalSecond-Time", "reciprocal second", None,
        external_ids={"ucum": "/s"},
    ),
    rec(
        "reciprocal cubic meter", "reciprocal\u00b7meter\u00b3", None, "m\u207b\u00b3",
        "reciprocal cubic meters",
        "volumetric number density", {"L": -3}, 1.0,
        "reciprocal cubic meter", "SI",
        "reciprocalCubicMetre", "reciprocal cubic metre", None,
        alternate_unit=["reciprocal cubic metre"],
        external_ids={"ucum": "/m3"},
    ),
    rec(
        "reciprocal day", "reciprocal\u00b7day", None, "d\u207b\u00b9",
        "reciprocal days",
        "frequency", {"T": -1}, 1.1574074074074073e-5, "hertz", "other",
        "reciprocalDay", "reciprocal day", None,
    ),
    rec(
        "reciprocal hour", "reciprocal\u00b7hour", None, "h\u207b\u00b9",
        "reciprocal hours",
        "frequency", {"T": -1}, 0.0002777777777777778, "hertz", "other",
        "reciprocalHour", "reciprocal hour", None,
    ),
    rec(
        "reciprocal minute", "reciprocal\u00b7minute", None, "min\u207b\u00b9",
        "reciprocal minutes",
        "frequency", {"T": -1}, 0.016666666666666666, "hertz", "other",
        "reciprocalMinute-Time", "reciprocal minute", None,
    ),
    rec(
        "reciprocal year", "reciprocal\u00b7year", None, "a\u207b\u00b9",
        "reciprocal years",
        "frequency", {"T": -1}, 3.168808781402895e-8, "hertz", "other",
        "reciprocalYear", "reciprocal year", None,
    ),
    rec(
        "second squared", "second\u00b2", None, "s\u00b2",
        "seconds squared",
        "time squared", {"T": 2}, 1.0, "second squared", "SI",
        "second-TimeSquared", "second squared", None,
    ),
]


# ──────────────────────────────────────────────────────────────────────────────
# TIER 4: Domain-specific (14 new)
# ──────────────────────────────────────────────────────────────────────────────

PARSEC_M = 3.085678e16  # 1 parsec in meters
YEAR_S = 3.15576e7  # Julian year in seconds

TIER_4 = [
    rec(
        "gigaparsec", "gigaparsec", "giga", "Gpc", "gigaparsecs",
        "length", {"L": 1}, PARSEC_M * 1e9, "meter", "Astronomical",
        "gigaparsec", "gigaparsec",
        "The gigaparsec is a unit of length defined as 1.0e9 parsec.",
        external_ids={"ucum": "Gpc"},
    ),
    rec(
        "kiloparsec", "kiloparsec", "kilo", "kpc", "kiloparsecs",
        "length", {"L": 1}, PARSEC_M * 1e3, "meter", "Astronomical",
        "kiloparsec", "kiloparsec",
        "The kiloparsec is a unit of length defined as 1.0e3 parsec.",
        external_ids={"ucum": "kpc"},
    ),
    rec(
        "megaparsec", "megaparsec", "mega", "Mpc", "megaparsecs",
        "length", {"L": 1}, PARSEC_M * 1e6, "meter", "Astronomical",
        "megaparsec", "megaparsec",
        "The megaparsec is a unit of length defined as 1.0e6 parsec.",
        external_ids={"ucum": "Mpc"},
    ),
    rec(
        "gigayear", "gigayear", "giga", "Gyr", "gigayears",
        "time", {"T": 1}, YEAR_S * 1e9, "second", "Astronomical",
        "gigayear", "gigayear", None,
    ),
    rec(
        "magnitude", "magnitude", None, "mag", "magnitudes",
        "stellar brightness", {}, 1.0, "magnitude", "Astronomical",
        "magnitude", "magnitude",
        "The magnitude is a logarithmic measure of the brightness of celestial objects.",
    ),
    rec(
        "micromagnitude", "micromagnitude", "micro", "\u03bcmag", "micromagnitudes",
        "stellar brightness", {}, 1e-6, "magnitude", "Astronomical",
        "micromagnitude", "micromagnitude",
        "The micromagnitude is a unit of magnitude defined as 1.0e-6 magnitude.",
    ),
    rec(
        "millimagnitude", "millimagnitude", "milli", "mmag", "millimagnitudes",
        "stellar brightness", {}, 1e-3, "magnitude", "Astronomical",
        "millimagnitude", "millimagnitude",
        "The millimagnitude is a unit of magnitude defined as 1.0e-3 magnitude.",
    ),
    rec(
        "millisecond of arc", "millisecond\u00b7of\u00b7arc", "milli", "mas",
        "milliseconds of arc",
        "angle", {}, 4.84813681109536e-9, "radian", "Astronomical",
        "millisecond-Angle", "millisecond (angle)",
        "The millisecond (angle) is a unit of angle defined as 1.0e-3 second (angle).",
        external_ids={"ucum": "''"},
    ),
    rec(
        "dozen", "dozen", None, "doz", "dozens",
        "ratio", {}, 12.0, "one", "other",
        "dozen", "dozen",
        "Dozen is a unit of dimension one defined as 12.",
    ),
    rec(
        "gross", "gross", None, "gro", "gross",
        "ratio", {}, 144.0, "one", "other",
        "gross", "gross",
        "Gross is a unit of dimension one defined as 144.",
    ),
    rec(
        "half dozen", "half\u00b7dozen", None, "half doz", "half dozens",
        "ratio", {}, 6.0, "one", "other",
        "halfDozen", "half dozen",
        "Half dozen is a unit of dimension one defined as 6.",
    ),
    rec(
        "hundred count", "hundred\u00b7count", None, "100", "hundred counts",
        "ratio", {}, 100.0, "one", "other",
        "hundredCount", "hundred count",
        "Hundred count is a unit of dimension one defined as 100.",
    ),
    rec(
        "thousand piece", "thousand\u00b7piece", None, "1000", "thousand pieces",
        "ratio", {}, 1000.0, "one", "other",
        "thousandPiece", "thousand piece",
        "Thousand piece is a unit of dimension one defined as 1000.",
    ),
    rec(
        "cicero", "cicero", None, "cc", "ciceros",
        "length", {"L": 1}, 0.004512, "meter", "other",
        "cicero", "cicero",
        "The cicero is a unit of length defined as 12 Didot points (approximately 4.512 mm).",
    ),
    rec(
        "decibar", "decibar", "deci", "dbar", "decibars",
        "pressure", {"M": 1, "L": -1, "T": -2}, 10000.0, "pascal", "Metric",
        "decibar", "decibar",
        "The decibar is a unit of pressure defined as 1.0e-1 bar.",
        external_ids={"ucum": "dbar"},
    ),
]


ALL_NEW = TIER_1 + TIER_2 + TIER_3 + TIER_4


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    canonical = root / "jsonl" / "units_of_measurement.jsonl"

    # Load existing records
    existing = []
    for line in canonical.read_text(encoding="utf-8").splitlines():
        if line.strip():
            existing.append(json.loads(line))
    print(f"Existing records: {len(existing)}")

    # Check for duplicates
    existing_keys = {(r["unit"], r["property"]) for r in existing}
    to_add = []
    for r in ALL_NEW:
        key = (r["unit"], r["property"])
        if key in existing_keys:
            print(f"  SKIP (already exists): {key}")
        else:
            to_add.append(r)
            existing_keys.add(key)

    if not to_add:
        print("No new records to add.")
        return 0

    print(f"Adding {len(to_add)} new records")

    # Merge and sort by property
    merged = existing + to_add
    merged.sort(key=lambda r: r["property"])

    # Write back
    lines = [json.dumps(r, ensure_ascii=False) for r in merged]
    canonical.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(merged)} total records to {canonical}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
