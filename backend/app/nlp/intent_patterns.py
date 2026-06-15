"""
intent_patterns.py
==================
CarbonTracker AI — Phase A Intent Detection Engine
All keyword patterns, scoring weights, and priority rules.

Design
------
Each intent has a dictionary of {phrase: weight} where:

  weight 5  — primary action verb (unambiguous intent signal)
               e.g. "ran", "bought", "disposed"
  weight 3  — secondary verb or strong compound phrase
               e.g. "drove", "charged", "recycled"
  weight 2  — strong noun / context word
               e.g. "biriyani", "plastic waste", "electricity"
  weight 1  — supporting noun (present in multiple categories)
               e.g. "laptop", "rice", "bag"

Longer phrases are tried before shorter ones (longest-match-first).
Every pattern is lowercased — the engine lowercases input before matching.

Extending this file is the ONLY change needed to improve intent accuracy.
Do not modify intent_engine.py for coverage changes.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Priority order — lower index = higher priority
# ---------------------------------------------------------------------------
INTENT_PRIORITY: list[str] = [
    "exercise",
    "transport",
    "food",
    "energy",
    "shopping",
    "waste",
]

# ---------------------------------------------------------------------------
# Minimum confidence to declare a winner (below this → "unknown")
# ---------------------------------------------------------------------------
CONFIDENCE_THRESHOLD: float = 0.42

# ---------------------------------------------------------------------------
# Intent 1 — Exercise
# ---------------------------------------------------------------------------
EXERCISE_PATTERNS: dict[str, int] = {
    # Primary verbs / activities (5)
    "ran":              5,
    "run":              5,
    "running":          5,
    "walked":           5,
    "walk":             5,
    "walking":          5,
    "jogged":           5,
    "jog":              5,
    "jogging":          5,
    "cycled":           5,
    "cycle":            5,
    "cycling":          5,
    "swam":             5,
    "swim":             5,
    "swimming":         5,
    "exercised":        5,
    "exercise":         5,
    "workout":          5,
    "worked out":       5,
    "trekked":          5,
    "trek":             5,
    "trekking":         5,
    "hiked":            5,
    "hike":             5,
    "hiking":           5,
    # Mind-body & gym activities (5)
    "yoga":             5,
    "yoga session":     5,
    "surya namaskar":   5,
    "meditation":       5,
    "meditated":        5,
    "stretching":       5,
    "stretched":        5,
    "gym":              5,
    "gym session":      5,
    "pilates":          5,
    "zumba":            5,
    "aerobics":         5,
    "crossfit":         5,
    "calisthenics":     5,
    "fitness":          5,
    # Compound phrases (3)
    "bicycle ride":     3,
    "morning walk":     3,
    "evening walk":     3,
    "morning run":      3,
    "went for a run":   3,
    "went for a walk":  3,
    "went for a jog":   3,
    # Context nouns (1)
    "bicycle":          1,
    "pedal":            1,
    "steps":            1,
}

# ---------------------------------------------------------------------------
# Intent 2 — Transport
# ---------------------------------------------------------------------------
TRANSPORT_PATTERNS: dict[str, int] = {
    # Primary verbs (5)
    "travelled":        5,
    "traveled":         5,
    "commuted":         5,
    "flew":             5,
    "boarded":          5,
    "drove":            5,
    "rode":             5,
    # Secondary verbs / phrases (3)
    "travel":           3,
    "commute":          3,
    "journey":          3,
    "trip":             3,
    "drive":            3,
    "ride":             3,
    "fly":              3,
    "took a flight":    3,
    "took the":         3,
    "took a":           3,
    "by train":         3,
    "by bus":           3,
    "by car":           3,
    "by flight":        3,
    "by metro":         3,
    "by bike":          3,
    "by auto":          3,
    "electric train":   3,
    "electric bus":     3,
    "electric car":     3,
    # Nouns (2)
    "flight":           2,
    "airplane":         2,
    "aircraft":         2,
    "metro":            2,
    "subway":           2,
    "ferry":            2,
    "ship":             2,
    "bus":              2,
    "train":            2,
    "taxi":             2,
    "cab":              2,
    "auto":             2,
    # Supporting (1)
    "motorcycle":       1,
    "scooter":          1,
    "car":              1,
    "bike":             1,
    "vehicle":          1,
}

# ---------------------------------------------------------------------------
# Intent 3 — Food
# ---------------------------------------------------------------------------
FOOD_PATTERNS: dict[str, int] = {
    # Primary verbs (5)
    "ate":              5,
    "eat":              5,
    "eating":           5,
    "drank":            5,
    "drink":            5,
    "drinking":         5,
    "consumed":         5,
    "consume":          5,
    # Secondary (3)
    "had":              3,
    "have":             3,
    "cooked":           3,
    "cook":             3,
    "ordered food":     3,
    "ordered from":     3,
    "breakfast":        3,
    "lunch":            3,
    "dinner":           3,
    "meal":             3,
    "snack":            3,
    "food":             3,
    "restaurant":       3,
    # Strong food nouns (2)
    "biriyani":         2,
    "biryani":          2,
    "briyani":          2,
    "rice":             2,
    "dosa":             2,
    "idli":             2,
    "idly":             2,
    "noodles":          2,
    "sambar":           2,
    "rasam":            2,
    "coffee":           2,
    "tea":              2,
    "juice":            2,
    "cake":             2,
    "chocolate":        2,
    "sweets":           2,
    "candy":            2,
    "biscuit":          2,
    "chips":            2,
    "pizza":            2,
    "burger":           2,
    "chicken":          2,
    "mutton":           2,
    "fish":             2,
    "egg":              2,
    # Supporting (1)
    "paneer":           1,
    "milk":             1,
    "bread":            1,
    "salad":            1,
}

# ---------------------------------------------------------------------------
# Intent 4 — Energy
# ---------------------------------------------------------------------------
ENERGY_PATTERNS: dict[str, int] = {
    # Primary verbs (5)
    "charged":          5,
    "charge":           5,
    "charging":         5,
    "plugged in":       5,
    "switched on":      5,
    "turned on":        5,
    "left on":          5,
    "left running":     5,
    "powered":          5,
    "operated":         5,
    # Secondary (3)
    "used":             3,
    "using":            3,
    "running":          3,
    "left on":          3,
    "electricity":      3,
    "power":            3,
    "energy":           3,
    "kwh":              3,
    "watt":             3,
    "watts":            3,
    "kilowatt":         3,
    # Appliance nouns (2)
    "ac":               2,
    "air conditioner":  2,
    "fan":              2,
    "light":            2,
    "lights":           2,
    "bulb":             2,
    "tv":               2,
    "television":       2,
    "washing machine":  2,
    "refrigerator":     2,
    "fridge":           2,
    "laptop charging":  2,
    "mobile charging":  2,
    "charger":          2,
    "geyser":           2,
    "water heater":     2,
    # Supporting (1)
    "laptop":           1,
    "mobile":           1,
    "phone":            1,
    "computer":         1,
    "appliance":        1,
    "hours":            1,
}

# ---------------------------------------------------------------------------
# Intent 5 — Shopping
# ---------------------------------------------------------------------------
SHOPPING_PATTERNS: dict[str, int] = {
    # Primary verbs (5)
    "bought":           5,
    "buy":              5,
    "purchased":        5,
    "purchase":         5,
    "ordered":          5,
    "order":            5,
    "acquired":         5,
    "subscribed":       5,
    # Secondary (3)
    "shopping":         3,
    "shop":             3,
    "got a new":        3,
    "picked up":        3,
    "received":         3,
    "booked":           3,
    "new":              3,
    # Retail nouns (2)
    "shirt":            2,
    "shoes":            2,
    "jeans":            2,
    "dress":            2,
    "jacket":           2,
    "clothes":          2,
    "clothing":         2,
    "sneakers":         2,
    "phone":            2,
    "smartphone":       2,
    "iphone":           2,
    "tablet":           2,
    "furniture":        2,
    "sofa":             2,
    # Supporting (1)
    "laptop":           1,
    "computer":         1,
    "tv":               1,
    "bag":              1,
    "book":             1,
}

# ---------------------------------------------------------------------------
# Intent 6 — Waste
# ---------------------------------------------------------------------------
WASTE_PATTERNS: dict[str, int] = {
    # Primary verbs (5)
    "disposed":         5,
    "dispose":          5,
    "discarded":        5,
    "discard":          5,
    "dumped":           5,
    "dump":             5,
    "threw away":       5,
    "thrown away":      5,
    "threw":            5,
    "thrown":           5,
    # Secondary (3)
    "recycled":         3,
    "recycling":        3,
    "recycle":          3,
    "waste":            3,
    "garbage":          3,
    "trash":            3,
    "rubbish":          3,
    "littered":         3,
    "composted":        3,
    # Waste type nouns (2)
    "plastic waste":    2,
    "organic waste":    2,
    "food waste":       2,
    "e-waste":          2,
    "e waste":          2,
    "battery disposal": 2,
    "old laptop disposal": 2,
    "paper waste":      2,
    "glass waste":      2,
    # Supporting (1)
    "plastic":          1,
    "paper":            1,
    "cardboard":        1,
    "battery":          1,
    "batteries":        1,
}

# ---------------------------------------------------------------------------
# Multi-intent split patterns
# ---------------------------------------------------------------------------
MULTI_INTENT_SPLITTERS: list[str] = [
    " and also ",
    " as well as ",
    " along with ",
    " then ",
    " after that ",
    " also ",
    " and ",
    ", ",
]

# ---------------------------------------------------------------------------
# Convenience bundle — used by the engine
# ---------------------------------------------------------------------------
ALL_PATTERNS: dict[str, dict[str, int]] = {
    "exercise": EXERCISE_PATTERNS,
    "transport": TRANSPORT_PATTERNS,
    "food":      FOOD_PATTERNS,
    "energy":    ENERGY_PATTERNS,
    "shopping":  SHOPPING_PATTERNS,
    "waste":     WASTE_PATTERNS,
}
