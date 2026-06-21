# food_factors.py
# ==============================================================
# CarbonTracker AI — Phase C3 Food Carbon Engine
# Approved Food Emission Factors (kg CO₂e per serving)
#
# Source: CARBONTRACKER MASTER EMISSION FORMULA STANDARD — Section C
# Formula: Carbon (kg CO₂) = Servings × Food Factor
#
# Rules:
#   - Longest-phrase matching must be applied (e.g. "Chicken Biriyani" > "Chicken")
#   - Unknown food items must return {"error": "unknown_food_item"}
#   - No fallback or guessing allowed
# ==============================================================

from typing import Optional

# ── Core Factor Dictionary (canonical_key → factor) ─────────────────────────
# All keys are lowercase to enable case-insensitive matching.
FOOD_FACTORS: dict[str, float] = {

    # ── Vegetarian ───────────────────────────────────────────────────────────
    "vegetable salad":  0.20,
    "idli":             0.12,
    "idly":             0.12,
    "dosa":             0.18,
    "pongal":           0.25,
    "upma":             0.22,
    "sambar rice":      0.45,
    "rasam rice":       0.35,
    "curd rice":        0.40,
    "lemon rice":       0.42,
    "tomato rice":      0.43,
    "veg fried rice":   0.55,
    "veg noodles":      0.50,

    # ── Beverages ────────────────────────────────────────────────────────────
    "coffee":           0.08,
    "tea":              0.05,

    # ── Sweets & Desserts ────────────────────────────────────────────────────
    "chocolate":        0.25,
    "cake":             0.40,
    "ice cream":        0.30,
    "icecream":         0.30,
    "candy":            0.05,
    "sweets":           0.20,
    "sweet":            0.20,

    # ── Egg Based ────────────────────────────────────────────────────────────
    "egg rice":         0.80,
    "egg noodles":      0.85,
    "boiled egg":       0.35,
    "boiled eggs":      0.35,
    "omelette":         0.45,
    "omelet":           0.45,

    # ── Chicken Based ────────────────────────────────────────────────────────
    "chicken rice":     1.60,
    "chicken noodles":  1.70,
    "chicken biriyani": 2.50,
    "chicken biryani":  2.50,
    "chicken briyani":  2.50,
    "chicken burger":   2.20,
    "chicken pizza":    2.40,

    # ── Mutton Based ─────────────────────────────────────────────────────────
    "mutton rice":      3.00,
    "mutton biriyani":  3.50,
    "mutton biryani":   3.50,
    "mutton briyani":   3.50,
}

# ── Keyword Aliases (alternative spellings → canonical factor key) ───────────
# Enables flexible user input without modifying the factor table.
FOOD_ALIASES: dict[str, str] = {
    "sambar sadam":      "sambar rice",
    "rasam sadam":       "rasam rice",
    "plain dosa":        "dosa",
    "masala dosa":       "dosa",
    "paneer dosa":       "dosa",
    "idlis":             "idli",
    "curd-rice":         "curd rice",
    "fried rice":        "veg fried rice",
    "vegetable noodles": "veg noodles",
    "chai":              "tea",
    "cappuccino":        "coffee",
    "latte":             "coffee",
    "espresso":          "coffee",
    "ice-cream":         "ice cream",
    "chocolates":        "chocolate",
    "candies":           "candy",
}

# ── Lookup Index (sorted longest-first for longest-phrase matching) ──────────
# Combines the main FOOD_FACTORS keys and FOOD_ALIASES keys, then sorts by
# descending length so "chicken biriyani" is always tried before "chicken".
_ALL_KEYWORDS: list[tuple[str, str]] = []  # (keyword, canonical_key)

for _k in FOOD_FACTORS:
    _ALL_KEYWORDS.append((_k, _k))

for _alias, _canonical in FOOD_ALIASES.items():
    if _canonical in FOOD_FACTORS:
        _ALL_KEYWORDS.append((_alias, _canonical))

# Sort by descending keyword length → guarantees longest-phrase-first matching
_ALL_KEYWORDS.sort(key=lambda t: len(t[0]), reverse=True)

FOOD_KEYWORD_INDEX: list[tuple[str, str]] = _ALL_KEYWORDS


def get_food_factor(food_name: str) -> Optional[float]:
    """
    Returns the emission factor (kg CO₂ per serving) for a given food name.
    Performs an exact, case-insensitive lookup on the canonical factor table.

    Parameters
    ----------
    food_name : Canonical food key (e.g. "chicken biriyani")

    Returns
    -------
    float factor or None if not found.
    """
    return FOOD_FACTORS.get(food_name.lower().strip())


def lookup_food_from_text(text: str) -> Optional[dict]:
    """
    Searches free-form text for the longest matching food keyword.

    Uses whole-word boundary checks via regex to prevent false partial matches
    (e.g., "burger" should not match inside "hamburger" if not a known key).

    Returns
    -------
    dict:
        {
            "canonical_key": str,    # e.g. "chicken biriyani"
            "display_name":  str,    # e.g. "Chicken Biriyani"
            "factor":        float,  # e.g. 2.50
            "keyword_matched": str,  # e.g. "chicken biriyani"
        }
    or None if no food is matched.
    """
    import re
    text_lower = text.lower()

    for keyword, canonical_key in FOOD_KEYWORD_INDEX:
        # Use word-boundary regex for accurate whole-phrase matching
        pattern = re.compile(r'\b' + re.escape(keyword) + r'\b')
        if pattern.search(text_lower):
            factor = FOOD_FACTORS.get(canonical_key)
            if factor is None:
                continue
            return {
                "canonical_key":   canonical_key,
                "display_name":    canonical_key.title(),
                "factor":          factor,
                "keyword_matched": keyword,
            }
    return None
