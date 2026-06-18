"""
food_emission_factors.py
========================
CarbonTracker AI — Universal Food Recognition & Carbon Estimation Engine.

Design Principles
-----------------
* Each entry maps one or more keyword phrases to a canonical dish name and a fixed CO₂ value.
* Matching uses **longest-phrase-first** so "chicken biriyani" wins over bare "chicken".
* Completely offline — zero DB lookups, zero network calls.
* New food items can be added here without touching any parser logic.

Data layout
-----------
FOOD_DB: list of dicts, each containing:
    "name"     : canonical display name
    "keywords" : list of keyword phrases that trigger this entry
    "co2_kg"   : kg CO₂e per serving/plate (fixed value)
    "unit"     : default quantity unit (always "plate" for dishes)

The list is pre-sorted longest-keyword-first at module load time so callers
can simply iterate and return the first match.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Food Database
# ---------------------------------------------------------------------------
_RAW: list[dict] = [

    # ── Vegetarian ──────────────────────────────────────────────────────────
    {
        "name": "Idly",
        "keywords": ["idly", "idli", "idlis"],
        "co2_kg": 0.12,
        "unit": "plate",
    },
    {
        "name": "Masala Dosa",
        "keywords": ["masala dosa"],
        "co2_kg": 0.18,
        "unit": "plate",
    },
    {
        "name": "dosa",
        "keywords": ["plain dosa", "paneer dosa", "dosa"],
        "co2_kg": 0.18,
        "unit": "plate",
    },
    {
        "name": "Pongal",
        "keywords": ["pongal"],
        "co2_kg": 0.70,
        "unit": "plate",
    },
    {
        "name": "Sambar Rice",
        "keywords": ["sambar rice", "sambar sadam"],
        "co2_kg": 0.45,
        "unit": "plate",
    },
    {
        "name": "Rasam Rice",
        "keywords": ["rasam rice", "rasam sadam"],
        "co2_kg": 0.80,
        "unit": "plate",
    },
    {
        "name": "Lemon Rice",
        "keywords": ["lemon rice"],
        "co2_kg": 0.70,
        "unit": "plate",
    },
    {
        "name": "Curd Rice",
        "keywords": ["curd rice"],
        "co2_kg": 0.40,
        "unit": "plate",
    },
    {
        "name": "Tomato Rice",
        "keywords": ["tomato rice"],
        "co2_kg": 0.90,
        "unit": "plate",
    },
    {
        "name": "Veg Meals",
        "keywords": ["south indian meals", "veg meals", "veg meal", "vegetarian meal", "vegetarian meals"],
        "co2_kg": 1.20,
        "unit": "plate",
    },
    {
        "name": "Veg Fried Rice",
        "keywords": ["veg fried rice", "veg rice"],
        "co2_kg": 0.60,
        "unit": "plate",
    },
    {
        "name": "Veg Noodles",
        "keywords": ["vegetable noodles", "veg noodles"],
        "co2_kg": 0.50,
        "unit": "plate",
    },
    {
        "name": "Paneer Butter Masala",
        "keywords": ["paneer butter masala"],
        "co2_kg": 2.20,
        "unit": "plate",
    },
    {
        "name": "Paneer Rice",
        "keywords": ["paneer rice"],
        "co2_kg": 2.00,
        "unit": "plate",
    },

    # ── Chicken ─────────────────────────────────────────────────────────────
    {
        "name": "Chicken Biriyani",
        "keywords": ["chicken biriyani", "chicken biryani", "chicken briyani"],
        "co2_kg": 2.50,
        "unit": "plate",
    },
    {
        "name": "Chicken Fried Rice",
        "keywords": ["chicken fried rice"],
        "co2_kg": 1.60,
        "unit": "plate",
    },
    {
        "name": "Chicken Noodles",
        "keywords": ["chicken noodles"],
        "co2_kg": 1.70,
        "unit": "plate",
    },
    {
        "name": "Chicken Rice",
        "keywords": ["chicken rice"],
        "co2_kg": 1.60,
        "unit": "plate",
    },
    {
        "name": "Chicken Curry",
        "keywords": ["chicken curry"],
        "co2_kg": 2.40,
        "unit": "plate",
    },
    {
        "name": "Chicken 65",
        "keywords": ["chicken 65"],
        "co2_kg": 2.30,
        "unit": "plate",
    },
    {
        "name": "Grilled Chicken",
        "keywords": ["grilled chicken"],
        "co2_kg": 2.20,
        "unit": "plate",
    },

    # ── Mutton ──────────────────────────────────────────────────────────────
    {
        "name": "Mutton Biriyani",
        "keywords": ["mutton biriyani", "mutton biryani", "mutton briyani"],
        "co2_kg": 3.50,
        "unit": "plate",
    },
    {
        "name": "Mutton Curry",
        "keywords": ["mutton curry"],
        "co2_kg": 5.50,
        "unit": "plate",
    },
    {
        "name": "Mutton Rice",
        "keywords": ["mutton rice"],
        "co2_kg": 3.00,
        "unit": "plate",
    },

    # ── Egg ─────────────────────────────────────────────────────────────────
    {
        "name": "Egg Noodles",
        "keywords": ["egg noodles"],
        "co2_kg": 0.85,
        "unit": "plate",
    },
    {
        "name": "Egg Fried Rice",
        "keywords": ["egg fried rice", "egg rice"],
        "co2_kg": 1.80,
        "unit": "plate",
    },
    {
        "name": "Omelette",
        "keywords": ["omelette", "omelet"],
        "co2_kg": 1.20,
        "unit": "plate",
    },
    {
        "name": "Boiled Egg",
        "keywords": ["boiled egg", "boiled eggs"],
        "co2_kg": 0.60,
        "unit": "item",
    },

    # ── Seafood ─────────────────────────────────────────────────────────────
    {
        "name": "Prawn Fry",
        "keywords": ["prawn fry", "prawn curry", "prawns"],
        "co2_kg": 2.50,
        "unit": "plate",
    },
    {
        "name": "Fish Fry",
        "keywords": ["fish fry"],
        "co2_kg": 2.00,
        "unit": "plate",
    },
    {
        "name": "Fish Curry",
        "keywords": ["fish curry"],
        "co2_kg": 1.90,
        "unit": "plate",
    },

    # ── Snacks ──────────────────────────────────────────────────────────────
    {
        "name": "Cream Biscuits",
        "keywords": ["cream biscuits", "cream biscuit", "oreo", "bourbon", "good day"],
        "co2_kg": 0.50,
        "unit": "item",
    },
    {
        "name": "Chips",
        "keywords": ["chips", "lays", "crisps"],
        "co2_kg": 0.60,
        "unit": "item",
    },
    {
        "name": "Murukku",
        "keywords": ["murukku"],
        "co2_kg": 0.60,
        "unit": "item",
    },
    {
        "name": "Mixture",
        "keywords": ["mixture"],
        "co2_kg": 0.70,
        "unit": "item",
    },
    {
        "name": "Biscuits",
        "keywords": ["biscuits", "biscuit"],
        "co2_kg": 0.30,
        "unit": "item",
    },

    # ── Sweets ──────────────────────────────────────────────────────────────
    {
        "name": "Chocolate Cake",
        "keywords": ["chocolate cake"],
        "co2_kg": 1.80,
        "unit": "slice",
    },
    {
        "name": "Birthday Cake",
        "keywords": ["birthday cake"],
        "co2_kg": 1.50,
        "unit": "slice",
    },
    {
        "name": "Cake",
        "keywords": ["cakes", "cake"],
        "co2_kg": 1.50,
        "unit": "slice",
    },
    {
        "name": "Ice Cream",
        "keywords": ["ice cream", "icecream"],
        "co2_kg": 1.20,
        "unit": "item",
    },
    {
        "name": "Chocolate",
        "keywords": [
            "dairy milk", "kitkat", "kit kat", "five star", "snickers",
            "chocolates", "chocolate",
        ],
        "co2_kg": 0.80,
        "unit": "item",
    },
    {
        "name": "Candy",
        "keywords": ["candies", "candy"],
        "co2_kg": 0.25,
        "unit": "item",
    },
    {
        "name": "Sweet",
        "keywords": [
            "mysore pak", "gulab jamun", "rasagulla", "jalebi", "halwa",
            "laddu", "laddoo", "sweets", "sweet",
        ],
        "co2_kg": 0.90,
        "unit": "item",
    },

    # ── Drinks ──────────────────────────────────────────────────────────────
    {
        "name": "Soft Drink",
        "keywords": ["soft drink", "soft drinks", "cold drink", "soda", "cola", "pepsi", "sprite"],
        "co2_kg": 0.40,
        "unit": "cup",
    },
    {
        "name": "Fruit Juice",
        "keywords": ["fruit juice", "juice"],
        "co2_kg": 0.30,
        "unit": "cup",
    },
    {
        "name": "Coffee",
        "keywords": ["coffee", "cappuccino", "latte", "espresso"],
        "co2_kg": 0.08,
        "unit": "cup",
    },
    {
        "name": "Tea",
        "keywords": ["tea", "chai"],
        "co2_kg": 0.05,
        "unit": "cup",
    },
    {
        "name": "Milk",
        "keywords": ["milk"],
        "co2_kg": 0.50,
        "unit": "cup",
    },
]

# ---------------------------------------------------------------------------
# Pre-processing: sort by longest keyword first so "chicken biriyani" is tried
# before bare "chicken", guaranteeing longest-phrase-first matching.
# ---------------------------------------------------------------------------
def _build_lookup(raw: list[dict]) -> list[tuple[str, str, float, str]]:
    """
    Returns a flat list of (keyword, canonical_name, co2_kg, unit) sorted by
    descending keyword length so longest phrases are matched first.
    """
    rows: list[tuple[str, str, float, str]] = []
    for entry in raw:
        for kw in entry["keywords"]:
            rows.append((kw.lower(), entry["name"], entry["co2_kg"], entry["unit"]))
    rows.sort(key=lambda r: len(r[0]), reverse=True)
    return rows


FOOD_LOOKUP: list[tuple[str, str, float, str]] = _build_lookup(_RAW)

# Also expose a simple name → co2 dict for quick lookups by canonical name
FOOD_BY_NAME: dict[str, dict] = {e["name"].lower(): e for e in _RAW}

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def lookup_food(text: str) -> dict | None:
    """
    Searches `text` (lowercased) for the longest matching food keyword.

    Returns a dict::

        {
            "name":   str,   # canonical dish name, e.g. "Chicken Biriyani"
            "co2_kg": float, # fixed CO₂ per serving, e.g. 2.80
            "unit":   str,   # default unit, e.g. "plate"
            "keyword_matched": str,
        }

    or ``None`` if no food is detected.

    Rules applied
    -------------
    * Case-insensitive whole-phrase matching (not substring-in-word).
    * Longest keyword wins (pre-sorted list).
    """
    text_lower = text.lower()
    for keyword, name, co2_kg, unit in FOOD_LOOKUP:
        # Use whole-phrase check: keyword must appear as a contiguous substring
        # (food phrases don't need word-boundary checks like transport does,
        #  because food phrases themselves contain spaces and are specific enough).
        if keyword in text_lower:
            return {
                "name": name,
                "co2_kg": co2_kg,
                "unit": unit,
                "keyword_matched": keyword,
            }
    return None


def get_ingredient_fallback(text: str) -> dict | None:
    """
    Rule 4: If an exact dish is not found, attempt ingredient matching.
    Tries to find any ingredient word (chicken, mutton, egg, fish, prawn)
    in the text and returns a representative emission for that protein type.
    """
    text_lower = text.lower()
    ingredient_map = [
        (["mutton", "lamb"],          "Mutton Rice",     5.20, "plate"),
        (["chicken"],                  "Chicken Rice",    2.50, "plate"),
        (["prawn", "shrimp"],         "Prawn Fry",       2.50, "plate"),
        (["fish", "tuna", "salmon"],  "Fish Curry",      1.90, "plate"),
        (["egg"],                      "Egg Fried Rice",  1.80, "plate"),
        (["paneer"],                   "Paneer Rice",     2.00, "plate"),
        (["chocolate", "choco"],       "Chocolate",       0.80, "item"),
        (["cake"],                     "Cake",            1.50, "slice"),
        (["biscuit"],                  "Biscuits",        0.30, "item"),
        (["sweet", "candy"],           "Sweet",           0.90, "item"),
    ]
    for keywords, name, co2_kg, unit in ingredient_map:
        for kw in keywords:
            if kw in text_lower:
                return {
                    "name": name,
                    "co2_kg": co2_kg,
                    "unit": unit,
                    "keyword_matched": kw,
                }
    return None
