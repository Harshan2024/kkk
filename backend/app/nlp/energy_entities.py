import re

ENERGY_ENTITIES = [
    "AC", "Air Conditioner", "Fan", "Laptop", "Laptop Charger", "Mobile Charger",
    "Refrigerator", "TV", "Washing Machine", "Light", "Water Heater", "Iron Box",
    "Mixer Grinder"
]

ENERGY_MAP = {e.lower(): e for e in ENERGY_ENTITIES}

def match_energy(text: str) -> dict:
    """
    Matches an energy device using longest phrase matching.
    Returns:
    {
      "entity": str,
      "raw_match": str
    } or empty dict.
    """
    cleaned = text.lower()
    sorted_keys = sorted(ENERGY_MAP.keys(), key=len, reverse=True)
    
    for key in sorted_keys:
        pattern = re.compile(rf"\b{re.escape(key)}\b")
        if pattern.search(cleaned):
            return {
                "entity": ENERGY_MAP[key],
                "raw_match": key
            }
            
    return {}
