import re

SYNONYMS = {
    "briyani": "biriyani",
    "biryani": "biriyani",
    "vegitarian": "vegetarian",
    "vegetable noodles": "veg noodles",
    "ecycle bike": "electric bike",
    "ecycle": "electric cycle",
    "chiken": "chicken",
    "ran": "running",
    "run": "running",
    "walked": "walking",
    "walk": "walking",
    "jogged": "jogging",
    "jog": "jogging",
    "cycled": "cycling",
    "cycle": "cycling",
    "swam": "swimming",
    "swim": "swimming",
}

def normalize_synonyms(text: str) -> str:
    """
    Normalizes spelling variations and shorthand expressions prior to entity matching.
    """
    cleaned = text.lower().strip()
    
    # Sort keys by length descending to match longest phrases first
    sorted_keys = sorted(SYNONYMS.keys(), key=len, reverse=True)
    for key in sorted_keys:
        val = SYNONYMS[key]
        pattern = re.compile(rf"\b{re.escape(key)}\b")
        cleaned = pattern.sub(val, cleaned)
        
    return cleaned
