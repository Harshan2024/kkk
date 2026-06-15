import re

SHOPPING_ENTITIES = [
    "Laptop", "Smartphone", "Tablet", "Television", "Refrigerator", "Washing Machine",
    "T-Shirt", "Shirt", "Jeans", "Shoes", "Bicycle", "Electric Bike"
]

SHOPPING_MAP = {s.lower(): s for s in SHOPPING_ENTITIES}

def match_shopping(text: str) -> dict:
    """
    Matches a shopping product using longest phrase matching.
    Returns:
    {
      "entity": str,
      "raw_match": str
    } or empty dict.
    """
    cleaned = text.lower()
    sorted_keys = sorted(SHOPPING_MAP.keys(), key=len, reverse=True)
    
    for key in sorted_keys:
        pattern = re.compile(rf"\b{re.escape(key)}\b")
        if pattern.search(cleaned):
            return {
                "entity": SHOPPING_MAP[key],
                "raw_match": key
            }
            
    return {}
