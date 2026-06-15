import re

TAMIL_NADU_CITIES = [
    "Chennai", "Madurai", "Coimbatore", "Salem", "Erode", "Trichy", "Tirunelveli"
]

INDIA_CITIES = [
    "Bangalore", "Hyderabad", "Mumbai", "Delhi", "Kolkata", "Pune", "Ahmedabad", "Kochi", "Vijayawada"
]

ALL_CITIES = TAMIL_NADU_CITIES + INDIA_CITIES

# Precompile lookup mapping (lowercase -> Canonical)
CITIES_LOWER = {c.lower(): c for c in ALL_CITIES}

def extract_cities(text: str) -> dict:
    """
    Extracts source and destination cities from transit routes:
    - Chennai to Madurai
    - from Chennai to Madurai
    - travelled Chennai-Madurai / Chennai - Madurai
    
    Returns {'source': str, 'destination': str} or empty dict.
    """
    cleaned = text.lower()
    
    # Compile pattern for all cities, longest first to prevent prefix hijacking
    sorted_city_keys = sorted(CITIES_LOWER.keys(), key=len, reverse=True)
    city_pattern = "|".join(re.escape(c) for c in sorted_city_keys)
    
    # 1. from [city] to [city] or [city] to [city]
    pattern_a = re.compile(rf"\b(?:from\s+)?({city_pattern})\s+to\s+({city_pattern})\b")
    match_a = pattern_a.search(cleaned)
    if match_a:
        c1, c2 = match_a.groups()
        return {
            "source": CITIES_LOWER[c1.lower()],
            "destination": CITIES_LOWER[c2.lower()]
        }
        
    # 2. [city]-[city] or [city] - [city]
    pattern_b = re.compile(rf"\b({city_pattern})\s*-\s*({city_pattern})\b")
    match_b = pattern_b.search(cleaned)
    if match_b:
        c1, c2 = match_b.groups()
        return {
            "source": CITIES_LOWER[c1.lower()],
            "destination": CITIES_LOWER[c2.lower()]
        }
        
    # Fallback: Find any cities mentioned in order of appearance
    found_cities = []
    for city_lower, canonical in CITIES_LOWER.items():
        for match in re.finditer(rf"\b{re.escape(city_lower)}\b", cleaned):
            found_cities.append((match.start(), canonical))
            
    found_cities.sort()
    if len(found_cities) >= 2:
        # Avoid duplicate city mapping if same city mentioned twice (unless they are distinct occurrences)
        return {
            "source": found_cities[0][1],
            "destination": found_cities[1][1]
        }
        
    return {}
