import re

# Canonical synonym mapping dictionary
SYNONYM_MAPPINGS = {
    # Exercise
    "run": "running",
    "ran": "running",
    "running": "running",
    "walk": "walking",
    "walked": "walking",
    "walking": "walking",
    "jog": "jogging",
    "jogged": "jogging",
    "jogging": "jogging",
    "cycle": "cycling",
    "cycled": "cycling",
    "cycling": "cycling",
    "bicycle": "cycling",
    # Appliances
    "ac": "air_conditioner",
    "air conditioner": "air_conditioner",
    "cooling": "air_conditioner",
    # Food (single-token)
    "veg meal": "vegetarian_food",
    "vegetarian": "vegetarian_food",
    "plant based": "vegetarian_food",
    # Transport
    "bike": "motorcycle",
    "motorcycle": "motorcycle",
    "scooter": "motorcycle",
}

# ---------------------------------------------------------------------------
# Food spelling normalisation rules
# These are applied BEFORE keyword matching so every variant maps to the
# canonical spelling that the food_emission_factors.py database uses.
# ---------------------------------------------------------------------------
FOOD_SPELLING_RULES: list[tuple[re.Pattern, str]] = [
    # biryani spelling variants — must come before generic word replacements
    (re.compile(r"\b(biriyani|briyani|biriani|biryani)\b", re.IGNORECASE), "biryani"),
    # noodle plural
    (re.compile(r"\bnoodle\b", re.IGNORECASE), "noodles"),
    # biscuit plural
    (re.compile(r"\bbiscuit\b", re.IGNORECASE), "biscuits"),
    # cake plural
    (re.compile(r"\bcakes\b", re.IGNORECASE), "cake"),
    # chocolate / choco shorthand
    (re.compile(r"\bchoco\b", re.IGNORECASE), "chocolate"),
    # chocolates → chocolate (singular lookup works)
    (re.compile(r"\bchocolates\b", re.IGNORECASE), "chocolate"),
    # sweet → sweets (the lookup key is "sweets")
    (re.compile(r"\bsweets?\b", re.IGNORECASE), "sweet"),
    # candy plural
    (re.compile(r"\bcandies\b", re.IGNORECASE), "candy"),
    # idly → idli
    (re.compile(r"\bidly\b", re.IGNORECASE), "idli"),
    # omelet → omelette
    (re.compile(r"\bomelet\b", re.IGNORECASE), "omelette"),
    # ice-cream without space
    (re.compile(r"\bicecream\b", re.IGNORECASE), "ice cream"),
    # kit-kat with hyphen
    (re.compile(r"\bkit-kat\b", re.IGNORECASE), "kit kat"),
    # laddoo → laddu
    (re.compile(r"\bladdoo\b", re.IGNORECASE), "laddu"),
]


def map_synonyms(text: str) -> str:
    """
    Normalizes spelling variations and mapped phrases to standard canonical tokens.

    Steps
    -----
    1. Apply food-specific spelling rules (regex, case-insensitive).
    2. Replace multi-word compound phrases.
    3. Replace single-token synonyms.

    Examples
    --------
    "I ate chicken biriyani"  → "I ate chicken biryani"
    "I had mutton briyani"    → "I had mutton biryani"
    "I ate chocolates"        → "I ate chocolate"
    "Why did my ac increase"  → "why did my air_conditioner increase"
    """
    # Step 1 — food spelling normalisation (preserves case context for display)
    for pattern, replacement in FOOD_SPELLING_RULES:
        text = pattern.sub(replacement, text)

    cleaned = text.lower().strip()

    # Step 2 — multi-word compound phrases
    cleaned = re.sub(r"\bair\s+conditioner\b", "air_conditioner", cleaned)
    cleaned = re.sub(r"\bveg\s+meal\b", "vegetarian_food", cleaned)
    cleaned = re.sub(r"\bplant\s+based\b", "vegetarian_food", cleaned)
    cleaned = re.sub(r"\bbike\s+ride\b", "cycling", cleaned)

    # Step 3 — single token replacement
    words = cleaned.split()
    mapped_words = []
    for w in words:
        if w in SYNONYM_MAPPINGS:
            mapped_words.append(SYNONYM_MAPPINGS[w])
        else:
            mapped_words.append(w)

    return " ".join(mapped_words)
