import re

# Pre-define unit aliases to canonical units
UNIT_MAPPINGS = {
    # Distance
    "km": "km", "kilometer": "km", "kilometre": "km", "mile": "miles", "miles": "miles",
    # Weight
    "kg": "kg", "kilogram": "kg", "g": "g", "gram": "g", "grams": "g",
    # Power
    "w": "W", "watt": "W", "watts": "W", "kw": "kW", "kilowatt": "kW",
    # Duration
    "min": "minutes", "mins": "minutes", "minute": "minutes", "minutes": "minutes",
    "hr": "hours", "hrs": "hours", "hour": "hours", "hours": "hours"
}

DISTANCE_UNITS = {"km", "miles"}
WEIGHT_UNITS = {"kg", "g"}
POWER_UNITS = {"W", "kW"}
DURATION_UNITS = {"minutes", "hours"}

def extract_quantities(text: str) -> list[dict]:
    """
    Parses a string and extracts all numeric quantities and units.
    Returns a list of dicts: [{"value": float/int, "unit": str, "raw_unit": str}]
    """
    sorted_units = sorted(UNIT_MAPPINGS.keys(), key=len, reverse=True)
    units_pattern = "|".join(re.escape(u) for u in sorted_units)
    
    # Matches a number (integer or float) followed optionally by spaces and the unit
    pattern = re.compile(
        rf"\b(\d+(?:\.\d+)?)\s*({units_pattern})\b",
        re.IGNORECASE
    )
    
    matches = pattern.findall(text)
    results = []
    for val_str, unit_str in matches:
        val = float(val_str)
        if val.is_integer():
            val = int(val)
        
        canonical_unit = UNIT_MAPPINGS[unit_str.lower()]
        results.append({
            "value": val,
            "unit": canonical_unit,
            "raw_unit": unit_str
        })
        
    return results

def extract_distance(text: str) -> dict:
    """Extracts distance and unit: returns {'distance': val, 'unit': str} or empty dict."""
    qs = extract_quantities(text)
    for q in qs:
        if q["unit"] in DISTANCE_UNITS:
            return {"distance": q["value"], "unit": q["unit"]}
    return {}

def extract_weight(text: str) -> dict:
    """Extracts weight and unit: returns {'weight': val, 'unit': str} or empty dict."""
    qs = extract_quantities(text)
    for q in qs:
        if q["unit"] in WEIGHT_UNITS:
            return {"weight": q["value"], "unit": q["unit"]}
    return {}

def extract_duration(text: str) -> dict:
    """Extracts duration and unit: returns {'duration': val, 'unit': str} or empty dict."""
    qs = extract_quantities(text)
    for q in qs:
        if q["unit"] in DURATION_UNITS:
            return {"duration": q["value"], "unit": q["unit"]}
    return {}

def extract_power(text: str) -> dict:
    """Extracts power and unit: returns {'power': val, 'unit': str} or empty dict."""
    qs = extract_quantities(text)
    for q in qs:
        if q["unit"] in POWER_UNITS:
            return {"power": q["value"], "unit": q["unit"]}
    return {}
