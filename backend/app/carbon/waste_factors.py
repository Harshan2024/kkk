# waste_factors.py
# ==============================================================
# CarbonTracker AI - Phase C4 Waste Carbon Engine
# Approved Waste Emission Factors (kg CO2e per kg of waste)
#
# Source: CARBONTRACKER MASTER EMISSION FORMULA STANDARD - Section E
# Formula: Carbon (kg CO2) = Weight (kg) x Factor
#
# Rules:
#   - Longest-phrase matching applied (e.g. "Plastic Waste" > "Plastic")
#   - Unknown waste types must return {"error": "unknown_waste_type"}
#   - No fallback or guessing allowed
# ==============================================================

from typing import Optional
import re

# ── Core Factor Dictionary (canonical_key -> factor) ────────────────────────
# All keys are lowercase to enable case-insensitive matching.
WASTE_FACTORS: dict[str, float] = {
    "plastic waste":    6.0,
    "e-waste":          12.0,
    "electronic waste": 12.0,
    "battery waste":    15.0,
    "organic waste":    0.5,
    "food waste":       0.8,
    "paper waste":      1.3,
    "glass waste":      0.9,
    "metal waste":      2.1,
}

# ── Alias Table (alternative phrase -> canonical key) ───────────────────────
# Maps common user phrases to their canonical factor key.
# Never maps to a made-up or estimated factor.
WASTE_ALIASES: dict[str, str] = {
    "electronic waste":   "e-waste",
    "electronics waste":  "e-waste",
    "mobile waste":       "e-waste",
    "laptop waste":       "e-waste",
    "phone waste":        "e-waste",
    "computer waste":     "e-waste",
    "device waste":       "e-waste",
    "ewaste":             "e-waste",
    "e waste":            "e-waste",
    "kitchen waste":      "organic waste",
    "vegetable waste":    "organic waste",
    "fruit waste":        "organic waste",
    "bio waste":          "organic waste",
    "biodegradable waste":"organic waste",
    "leftover waste":     "food waste",
    "food scraps":        "food waste",
}

# ── Lookup Index (sorted longest-first for longest-phrase matching) ──────────
# Combines canonical WASTE_FACTORS keys and WASTE_ALIASES keys,
# sorted descending by length so longer phrases are always tried first.
_ALL_KEYWORDS: list[tuple[str, str]] = []  # (keyword, canonical_key)

for _k in WASTE_FACTORS:
    _ALL_KEYWORDS.append((_k, _k))

for _alias, _canonical in WASTE_ALIASES.items():
    if _canonical in WASTE_FACTORS:
        _ALL_KEYWORDS.append((_alias, _canonical))

# Sort descending by keyword length -> longest phrase wins
_ALL_KEYWORDS.sort(key=lambda t: len(t[0]), reverse=True)

WASTE_KEYWORD_INDEX: list[tuple[str, str]] = _ALL_KEYWORDS

# ── Display Names (canonical_key -> Display Name) ───────────────────────────
WASTE_DISPLAY_NAMES: dict[str, str] = {
    "plastic waste":    "Plastic Waste",
    "e-waste":          "E-Waste",
    "electronic waste": "E-Waste",
    "battery waste":    "Battery Waste",
    "organic waste":    "Organic Waste",
    "food waste":       "Food Waste",
    "paper waste":      "Paper Waste",
    "glass waste":      "Glass Waste",
    "metal waste":      "Metal Waste",
}


def get_waste_factor(waste_type: str) -> Optional[float]:
    """
    Returns the emission factor (kg CO2 per kg waste) for a given waste type.
    Performs exact, case-insensitive lookup on the canonical factor table.

    Parameters
    ----------
    waste_type : Canonical waste key (e.g. "plastic waste")

    Returns
    -------
    float factor or None if not found.
    """
    return WASTE_FACTORS.get(waste_type.lower().strip())


def lookup_waste_from_text(text: str) -> Optional[dict]:
    """
    Searches free-form text for the longest matching waste keyword.

    Uses whole-word boundary regex to prevent false partial matches.

    Returns
    -------
    dict:
        {
            "canonical_key":   str,   # e.g. "plastic waste"
            "display_name":    str,   # e.g. "Plastic Waste"
            "factor":          float, # e.g. 6.0
            "keyword_matched": str,   # e.g. "plastic waste"
        }
    or None if no waste type is matched.
    """
    text_lower = text.lower()

    for keyword, canonical_key in WASTE_KEYWORD_INDEX:
        pattern = re.compile(r'\b' + re.escape(keyword) + r'\b')
        if pattern.search(text_lower):
            factor = WASTE_FACTORS.get(canonical_key)
            if factor is None:
                continue
            display = WASTE_DISPLAY_NAMES.get(canonical_key, canonical_key.title())
            return {
                "canonical_key":   canonical_key,
                "display_name":    display,
                "factor":          factor,
                "keyword_matched": keyword,
            }
    return None
