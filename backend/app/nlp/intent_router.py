"""
intent_router.py
================
CarbonTracker AI — Intent-First Parsing Engine.

Design
------
Detects the user's **verb / intent** before doing any entity matching,
so that the same noun ("laptop") maps to different categories depending
on what the user actually *did* with it:

    "I bought a laptop"            → Shopping  (200 kg CO₂)
    "I charged my laptop 1 hour"   → Energy    (0.05 kg CO₂)

Rules
-----
- Shopping verbs always win over appliance/transport noun matching.
- Energy verbs + appliance noun → appliances / energy.
- Transport verbs + city route  → transport (city-distance lookup).
- Food verbs → food (never transport, never shopping).
- Exercise verbs → exercise (zero emissions).
- Wattage detection overrides appliance power-table lookup.
"""

from __future__ import annotations
import re

# ---------------------------------------------------------------------------
# Intent → Verb sets
# ---------------------------------------------------------------------------
SHOPPING_VERBS: frozenset[str] = frozenset({
    "buy", "bought", "purchase", "purchased", "ordered", "order", "got",
    "picked", "grabbed", "acquired", "shopped",
})

ENERGY_VERBS: frozenset[str] = frozenset({
    "use", "used", "charge", "charged", "charging", "plug", "plugged",
    "running", "operated", "powered", "switched", "turned",
})

TRANSPORT_VERBS: frozenset[str] = frozenset({
    "travel", "travelled", "traveled", "went", "go",
    "drove", "drive", "rode", "ride", "commuted", "commute",
    "flew", "fly", "took", "taken", "boarded", "caught",
    "journeyed", "trip",
})

FOOD_VERBS: frozenset[str] = frozenset({
    "ate", "eat", "eating", "had", "have", "consumed", "consume",
    "drank", "drink", "drinking", "cooked", "cook", "ordered",
    "tasted", "enjoyed",
})

EXERCISE_VERBS: frozenset[str] = frozenset({
    "ran", "run", "running", "walked", "walk", "walking",
    "jogged", "jog", "jogging", "cycled", "cycle", "cycling",
    "swam", "swim", "swimming", "exercised", "exercise", "workout",
    # Mind-body & gym
    "yoga", "meditation", "meditated", "stretching", "stretched",
    "gym", "pilates", "zumba", "aerobics", "crossfit", "calisthenics",
    "fitness", "trekked", "trek", "trekking", "hiked", "hike", "hiking",
})


# ---------------------------------------------------------------------------
# Indian + International city-to-city road/rail distances (km)
# ---------------------------------------------------------------------------
CITY_DISTANCES: dict[tuple[str, str], int] = {
    # ── Tamil Nadu ──────────────────────────────────────────────────────────
    ("chennai", "madurai"):       462,
    ("chennai", "coimbatore"):    496,
    ("chennai", "trichy"):        330,
    ("chennai", "salem"):         340,
    ("chennai", "tirunelveli"):   631,
    ("chennai", "vellore"):       145,
    ("chennai", "pondicherry"):   162,
    ("madurai", "coimbatore"):    210,
    ("madurai", "trichy"):        135,
    ("madurai", "tirunelveli"):   162,
    ("coimbatore", "ooty"):        86,
    # ── South India ─────────────────────────────────────────────────────────
    ("chennai", "bangalore"):     350,
    ("chennai", "hyderabad"):     628,
    ("bangalore", "hyderabad"):   575,
    ("bangalore", "mysore"):      145,
    ("bangalore", "coimbatore"):  360,
    ("bangalore", "kochi"):       540,
    ("hyderabad", "vijayawada"):  275,
    # ── North India ─────────────────────────────────────────────────────────
    ("delhi", "agra"):            206,
    ("delhi", "jaipur"):          281,
    ("delhi", "lucknow"):         558,
    ("delhi", "chandigarh"):      248,
    ("delhi", "amritsar"):        449,
    ("delhi", "varanasi"):        822,
    ("delhi", "patna"):           1000,
    # ── West India ──────────────────────────────────────────────────────────
    ("mumbai", "pune"):           149,
    ("mumbai", "nashik"):         167,
    ("mumbai", "ahmedabad"):      524,
    ("mumbai", "surat"):          284,
    # ── International (air) ─────────────────────────────────────────────────
    ("chennai", "delhi"):        1750,
    ("delhi", "chennai"):        1750,
    ("delhi", "mumbai"):         1150,
    ("mumbai", "delhi"):         1150,
    ("bangalore", "delhi"):      1700,
    ("delhi", "bangalore"):      1700,
    ("chennai", "bangalore"):     290,  # air
    ("bangalore", "chennai"):     290,
    ("mumbai", "bangalore"):      850,
    ("bangalore", "mumbai"):      850,
    ("mumbai", "chennai"):       1030,
    ("chennai", "mumbai"):       1030,
    ("london", "new york"):      5570,
    ("new york", "london"):      5570,
    ("new york", "los angeles"): 3940,
    ("los angeles", "new york"): 3940,
    ("dubai", "mumbai"):         1934,
    ("mumbai", "dubai"):         1934,
    ("singapore", "chennai"):    2892,
    ("chennai", "singapore"):    2892,
}

# ---------------------------------------------------------------------------
# Vehicle emission factors (kg CO₂/km) — used when not found in DB
# ---------------------------------------------------------------------------
VEHICLE_EMISSION_FACTORS: dict[str, float] = {
    "electric train":   0.020,
    "train":            0.041,
    "diesel train":     0.041,
    "metro":            0.009,
    "subway":           0.009,
    "electric bus":     0.035,
    "bus":              0.089,
    "petrol car":       0.192,
    "diesel car":       0.171,
    "ev":               0.050,
    "electric car":     0.050,
    "bike":             0.113,
    "motorcycle":       0.113,
    "scooter":          0.113,
    "flight":           0.255,
    "plane":            0.255,
    "auto":             0.132,
    "walking":          0.000,
    "cycling":          0.000,
}

# Shopping item → kg CO₂ (lifecycle / manufacturing emissions)
SHOPPING_EMISSION_KG: dict[str, float] = {
    "laptop":        200.0,
    "computer":      300.0,
    "desktop":       300.0,
    "phone":         70.0,
    "smartphone":    70.0,
    "iphone":        70.0,
    "tablet":        130.0,
    "tv":            250.0,
    "television":    250.0,
    "monitor":       100.0,
    "printer":       80.0,
    "camera":        60.0,
    "headphones":    15.0,
    "earphones":     8.0,
    "smartwatch":    25.0,
    "washing machine": 150.0,
    "refrigerator":  400.0,
    "fridge":        400.0,
    "air conditioner": 700.0,
    "ac":            700.0,
    "microwave":     80.0,
    "vacuum cleaner": 50.0,
    "shirt":         3.0,
    "t-shirt":       3.0,
    "jeans":         8.0,
    "dress":         5.0,
    "shoes":         10.0,
    "sneakers":      14.0,
    "jacket":        10.0,
    "coat":          15.0,
    "bag":           5.0,
    "backpack":      7.0,
    "book":          1.5,
    "furniture":     90.0,
    "sofa":          200.0,
    "chair":         40.0,
    "bicycle":       96.0,
    "car":           6000.0,
}

# Grid electricity emission factor (kg CO₂/kWh) — fallback
GRID_FACTOR_KG_PER_KWH: float = 0.82   # India average


def detect_intent(text: str) -> str | None:
    """
    Scans `text` (already lowercased) for intent-bearing verbs.

    Returns one of: 'shopping', 'energy', 'transport', 'food', 'exercise'
    or None if no intent verb is found.

    Priority: exercise > shopping > food > transport > energy
    (exercise first to prevent "went for a run" → transport)
    """
    words = set(re.findall(r'\b\w+\b', text.lower()))

    if words & EXERCISE_VERBS:
        return "exercise"
    if words & SHOPPING_VERBS:
        # Extra guard: "ordered" food is food intent
        # If food verb also present and food context stronger, treat as food
        if words & FOOD_VERBS and _has_food_noun(text):
            return "food"
        return "shopping"
    if words & FOOD_VERBS:
        return "food"
    if words & TRANSPORT_VERBS:
        return "transport"
    if words & ENERGY_VERBS:
        return "energy"
    return None


def _has_food_noun(text: str) -> bool:
    """Quick check for obvious food nouns to disambiguate 'ordered'."""
    food_indicators = [
        "biriyani", "biryani", "rice", "noodles", "dosa", "idli",
        "pizza", "burger", "chicken", "mutton", "fish", "food",
        "meal", "lunch", "dinner", "breakfast", "snack",
    ]
    text_lower = text.lower()
    return any(f in text_lower for f in food_indicators)


def detect_wattage(text: str) -> float | None:
    """
    Extracts explicit wattage from text.
    Patterns: '60W', '60 watt', '100W charger', '1500 watts'
    Returns watts as float, or None if not found.
    """
    patterns = [
        r'(\d+(?:\.\d+)?)\s*[Ww](?:att)?s?\b',
        r'(\d+(?:\.\d+)?)\s*-?\s*watt',
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return float(m.group(1))
    return None


def compute_wattage_emission(watts: float, hours: float,
                              grid_factor: float = GRID_FACTOR_KG_PER_KWH) -> tuple[float, dict]:
    """
    Computes CO₂ from explicit wattage.
    Formula: (W / 1000) × hours × grid_factor
    """
    kw = watts / 1000.0
    kwh = kw * hours
    co2 = kwh * grid_factor
    return co2, {
        "calculation_type": "wattage_based",
        "wattage_w": watts,
        "power_kw": round(kw, 4),
        "duration_hours": hours,
        "total_kwh": round(kwh, 4),
        "grid_emission_factor": grid_factor,
        "total_emissions_kg": round(co2, 4),
    }


def lookup_shopping_emission(text: str) -> tuple[str, float] | None:
    """
    Tries to find a shopping item in SHOPPING_EMISSION_KG by scanning text.
    Returns (item_name, co2_kg) or None.
    Longest match first.
    """
    text_lower = text.lower()
    # Sort by key length descending for longest match
    for item, co2 in sorted(SHOPPING_EMISSION_KG.items(), key=lambda x: -len(x[0])):
        if item in text_lower:
            return item, co2
    return None


def lookup_city_route(text: str, doc: Any = None) -> tuple[str, str, int] | None:
    """
    Scans text for a "from <city> to <city>" pattern and returns
    (city_a, city_b, distance_km) using CITY_DISTANCES.
    Returns None if no known route found.
    """
    # Try resolving via spaCy first
    try:
        from app.nlp.spacy_service import extract_source_destination
        route_info = extract_source_destination(doc if doc is not None else text)
        source = route_info.get("source")
        destination = route_info.get("destination")
        if source and destination:
            city_a = source.lower()
            city_b = destination.lower()
            key = (city_a, city_b)
            rev = (city_b, city_a)
            if key in CITY_DISTANCES:
                return city_a, city_b, CITY_DISTANCES[key]
            if rev in CITY_DISTANCES:
                return city_b, city_a, CITY_DISTANCES[rev]
            # Try partial matching for multi-word city names
            for (ca, cb), dist in CITY_DISTANCES.items():
                if (ca in city_a or city_a in ca) and (cb in city_b or city_b in cb):
                    return ca, cb, dist
                if (cb in city_a or city_a in cb) and (ca in city_b or city_b in ca):
                    return cb, ca, dist
    except Exception:
        pass

    # Regex Fallback
    patterns = [
        r'from\s+([a-z\s]+?)\s+to\s+([a-z\s]+?)(?:\s+by|\s+via|\s+using|\s+in|$)',
        r'([a-z\s]+?)\s+to\s+([a-z\s]+?)(?:\s+by|\s+via|\s+using|\s+in|$)',
    ]
    text_lower = text.lower().strip()
    for pattern in patterns:
        m = re.search(pattern, text_lower)
        if m:
            city_a = m.group(1).strip()
            city_b = m.group(2).strip()
            key = (city_a, city_b)
            rev = (city_b, city_a)
            if key in CITY_DISTANCES:
                return city_a, city_b, CITY_DISTANCES[key]
            if rev in CITY_DISTANCES:
                return city_b, city_a, CITY_DISTANCES[rev]
            # Try partial matching for multi-word city names
            for (ca, cb), dist in CITY_DISTANCES.items():
                if (ca in city_a or city_a in ca) and (cb in city_b or city_b in cb):
                    return ca, cb, dist
                if (cb in city_a or city_a in cb) and (ca in city_b or city_b in ca):
                    return cb, ca, dist
    return None


def detect_vehicle(text: str) -> str:
    """
    Detects transport vehicle type from text.
    Returns canonical vehicle name (matches VEHICLE_EMISSION_FACTORS keys).
    """
    text_lower = text.lower()
    # Longest-match order
    checks = [
        ("electric train", "electric train"),
        ("electric bus",   "electric bus"),
        ("diesel train",   "diesel train"),
        ("electric car",   "electric car"),
        ("petrol car",     "petrol car"),
        ("diesel car",     "diesel car"),
        ("auto rickshaw",  "auto"),
        ("metro",          "metro"),
        ("subway",         "subway"),
        ("flight",         "flight"),
        ("plane",          "plane"),
        ("airplane",       "flight"),
        ("aircraft",       "flight"),
        ("train",          "train"),
        ("bus",            "bus"),
        ("bike",           "bike"),
        ("motorcycle",     "bike"),
        ("scooter",        "bike"),
        ("ev",             "ev"),
        ("car",            "petrol car"),
        ("auto",           "auto"),
        ("walk",           "walking"),
        ("bicycle",        "cycling"),
        ("drove",          "petrol car"),
        ("drive",          "petrol car"),
        ("driving",        "petrol car"),
        ("commuted",       "petrol car"),
        ("commute",        "petrol car"),
        ("flew",           "flight"),
        ("fly",            "flight"),
        ("flying",         "flight"),
        ("rode",           "bike"),
        ("ride",           "bike"),
        ("riding",         "bike"),
    ]
    for keyword, canonical in checks:
        if keyword in text_lower:
            return canonical
    return "unknown_transport_mode"  # default
