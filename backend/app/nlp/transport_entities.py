import re

TRANSPORT_ENTITIES = [
    "Car", "Petrol Car", "Diesel Car", "CNG Car", "Hybrid Car", "Electric Car",
    "Bike", "Motorcycle", "Scooter", "Electric Scooter", "Electric Bike", "Bicycle",
    "Auto", "Taxi", "Cab", "Bus", "Electric Bus", "Train", "Electric Train", "Metro",
    "Flight", "Ferry", "Ship"
]

TRANSPORT_MAP = {t.lower(): t for t in TRANSPORT_ENTITIES}

def match_transport(text: str) -> dict:
    """
    Matches a transport entity using longest phrase matching.
    Returns:
    {
      "entity": str,
      "raw_match": str
    } or empty dict.
    """
    cleaned = text.lower()
    sorted_keys = sorted(TRANSPORT_MAP.keys(), key=len, reverse=True)
    
    for key in sorted_keys:
        pattern = re.compile(rf"\b{re.escape(key)}\b")
        if pattern.search(cleaned):
            return {
                "entity": TRANSPORT_MAP[key],
                "raw_match": key
            }
            
    # Verb fallback checks
    verb_fallbacks = [
        (re.compile(r"\b(drove|drive|driving)\b"), "Petrol Car", "drove"),
        (re.compile(r"\b(flew|fly|flying|flight)\b"), "Flight", "flew"),
        (re.compile(r"\b(rode|ride|riding)\b"), "Motorcycle", "rode"),
    ]
    
    triggered_entity = None
    triggered_raw = None
    for pattern, entity_name, raw_key in verb_fallbacks:
        if pattern.search(cleaned):
            triggered_entity = entity_name
            triggered_raw = raw_key
            break
            
    if triggered_entity:
        from app.nlp.city_database import CITIES_LOWER
        words = re.findall(r"\b[a-z]+\b", cleaned)
        
        # Stopwords, verbs, units, cities, etc.
        filter_words = {
            "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them", 
            "my", "your", "his", "its", "our", "their", "mine", "yours", "hers", "ours", "theirs",
            "a", "an", "the", "this", "that", "these", "those",
            "to", "from", "at", "by", "for", "with", "about", "against", "between", "into", "through", 
            "during", "before", "after", "above", "below", "of", "in", "on", "out", "off", "over", "under", "again", "further", "then", "once",
            "here", "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such",
            "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now",
            "km", "kms", "mile", "miles", "meter", "meters", "hour", "hours", "minute", "minutes", "day", "days", "week", "weeks",
            "yesterday", "today", "tomorrow", "morning", "afternoon", "evening", "night", "daily", "weekly", "yearly",
            "home", "work", "office", "school", "college", "university", "gym", "store", "shop", "market",
            "back", "forth", "around", "slowly", "fast", "quickly", "silently", "and", "or", "but",
            # Verbs
            "drove", "drive", "driving", "flew", "fly", "flying", "flight", "rode", "ride", "riding",
            "travelled", "traveled", "went", "go", "commuted", "commute", "took", "take", "taking",
            # Cities from database
            *CITIES_LOWER.keys()
        }
        
        unknown_words = [w for w in words if w not in filter_words]
        if unknown_words:
            return {}
            
        return {
            "entity": triggered_entity,
            "raw_match": triggered_raw
        }
        
    return {}
