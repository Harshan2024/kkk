import re

EXERCISE_ENTITIES = [
    "Running", "Jogging", "Walking", "Cycling", "Bicycle Ride", "Yoga",
    "Meditation", "Gym Workout", "Exercise", "Fitness", "Swimming",
    "Trekking", "Hiking", "Zumba", "Pilates", "Surya Namaskar", "Cricket"
]

EXERCISE_MAP = {e.lower(): e for e in EXERCISE_ENTITIES}

def match_exercise(text: str) -> dict:
    """
    Tries to match an exercise entity.
    Returns:
    {
      "entity": str,
      "raw_match": str
    } or empty dict.
    """
    cleaned = text.lower()
    sorted_keys = sorted(EXERCISE_MAP.keys(), key=len, reverse=True)
    
    for key in sorted_keys:
        pattern = re.compile(rf"\b{re.escape(key)}\b")
        if pattern.search(cleaned):
            return {
                "entity": EXERCISE_MAP[key],
                "raw_match": key
            }
            
    return {}
