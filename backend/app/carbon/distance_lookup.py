CITY_DISTANCE = {
    ("chennai", "madurai"): 462,
    ("madurai", "chennai"): 462,
    ("chennai", "bangalore"): 350,
    ("bangalore", "chennai"): 350,
    ("salem", "coimbatore"): 165,
    ("coimbatore", "salem"): 165,
    ("chennai", "delhi"): 1760,
    ("delhi", "chennai"): 1760
}

def lookup_distance(source: str, destination: str) -> int:
    """
    Looks up the distance between two cities case-insensitively.
    Returns the distance in km, or None if not found.
    """
    src = source.lower().strip()
    dst = destination.lower().strip()
    return CITY_DISTANCE.get((src, dst))
