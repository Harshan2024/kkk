import re

WASTE_ENTITIES = [
    "Plastic Waste", "Organic Waste", "Food Waste", "E-Waste", "Battery Waste",
    "Paper Waste", "Glass Waste", "Metal Waste"
]

WASTE_MAP = {w.lower(): w for w in WASTE_ENTITIES}
WASTE_MAP["e waste"] = "E-Waste"

def match_waste(text: str) -> dict:
    """
    Matches a waste type using longest phrase matching.
    Returns:
    {
      "entity": str,
      "raw_match": str
    } or empty dict.
    """
    cleaned = text.lower()
    sorted_keys = sorted(WASTE_MAP.keys(), key=len, reverse=True)
    
    for key in sorted_keys:
        pattern = re.compile(rf"\b{re.escape(key)}\b")
        if pattern.search(cleaned):
            return {
                "entity": WASTE_MAP[key],
                "raw_match": key
            }
            
    return {}
