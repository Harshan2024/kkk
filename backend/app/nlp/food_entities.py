import re

FOOD_ENTITIES = [
    "Chicken Biriyani", "Mutton Biriyani", "Egg Rice", "Egg Noodles", "Veg Noodles",
    "Chicken Noodles", "Sambar Rice", "Rasam Rice", "Lemon Rice", "Curd Rice",
    "Dosa", "Idli", "Pongal", "Coffee", "Tea", "Juice", "Cake", "Chocolate Cake",
    "Chocolate", "Candy", "Ice Cream", "Sweets", "Biscuits", "Cream Biscuits",
    "Biriyani"
]

FOOD_MAP = {f.lower(): f for f in FOOD_ENTITIES}

def match_food(text: str) -> dict:
    """
    Matches a food entity using longest phrase matching.
    Returns:
    {
      "entity": str,
      "raw_match": str
    } or empty dict.
    """
    cleaned = text.lower()
    sorted_keys = sorted(FOOD_MAP.keys(), key=len, reverse=True)
    
    for key in sorted_keys:
        pattern = re.compile(rf"\b{re.escape(key)}\b")
        if pattern.search(cleaned):
            return {
                "entity": FOOD_MAP[key],
                "raw_match": key
            }
            
    return {}
