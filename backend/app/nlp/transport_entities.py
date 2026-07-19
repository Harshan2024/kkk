import re

TRANSPORT_ENTITIES = [
    "Car", "Petrol Car", "Diesel Car", "CNG Car", "Hybrid Car", "Electric Car",
    "Bike", "Motorcycle", "Scooter", "Electric Scooter", "Electric Bike", "Bicycle",
    "Auto", "Taxi", "Cab", "Bus", "Electric Bus", "Train", "Electric Train", "Metro",
    "Flight", "Ferry", "Ship"
]

TRANSPORT_MAP = {t.lower(): t for t in TRANSPORT_ENTITIES}

def resolve_two_wheeler_context(text: str) -> dict | None:
    """
    Analyzes text to classify two-wheeler type (Motorcycle vs. Bicycle vs. Electric Bike/Scooter)
    based on context words, brands, and specified priorities.
    """
    cleaned = text.lower().strip()
    
    # Brand names: must always classify as Motorcycle
    brands = ["hero", "honda", "yamaha", "tvs", "bajaj", "royal enfield", "ktm", "suzuki"]
    has_brand = any(re.search(r'\b' + re.escape(brand) + r'\b', cleaned) for brand in brands)
    
    # Check for explicit compound strings
    has_petrol_bike = "petrol bike" in cleaned or "petrol motorcycle" in cleaned
    has_motor_bike = "motor bike" in cleaned or "motorbike" in cleaned
    has_electric_bike = "electric bike" in cleaned or "electric_bike" in cleaned
    has_electric_scooter = "electric scooter" in cleaned or "electric_scooter" in cleaned
    has_bicycle = "bicycle" in cleaned
    has_cycle = re.search(r'\bcycle\b|\bcycling\b|\bcycled\b', cleaned)
    
    # Generic keywords
    has_bike = re.search(r'\bbikes?\b', cleaned)
    has_scooter = re.search(r'\bscooters?\b', cleaned)
    has_motorcycle = "motorcycle" in cleaned or "motorcycles" in cleaned
    
    # Context checks using substring matches to be robust against pluralization/stemming
    has_petrol_ctx = any(p in cleaned for p in ["petrol", "fuel"])
    has_electric_ctx = any(e in cleaned for e in ["electric", "ev", "charge", "battery"])
    has_motorcycle_ctx = any(m in cleaned for m in ["helmet", "engine", "riding", "ride", "rode", "road"])
    has_bicycle_ctx = any(b in cleaned for b in ["pedal", "cycling", "cycle", "bicycle", "human"])
    
    # Rules application in order of priority:
    # 1. petrol bike
    if has_petrol_bike or (has_bike and has_petrol_ctx):
        return {
            "vehicle": "Petrol Motorcycle",
            "fuel_type": "Petrol",
            "vehicle_type": "Motorcycle",
            "item_key": "petrol motorcycle",
            "factor": 0.103,
            "source": "CarbonTracker Standard"
        }
        
    # 2. motor bike
    if has_motor_bike:
        return {
            "vehicle": "Motorcycle",
            "fuel_type": "Petrol",
            "vehicle_type": "Motorcycle",
            "item_key": "motorcycle",
            "factor": 0.103,
            "source": "CarbonTracker Standard"
        }
        
    # 3. motorcycle
    if has_motorcycle or has_brand:
        return {
            "vehicle": "Motorcycle",
            "fuel_type": "Petrol",
            "vehicle_type": "Motorcycle",
            "item_key": "motorcycle",
            "factor": 0.103,
            "source": "CarbonTracker Standard"
        }
        
    # 4. electric bike
    if has_electric_bike or (has_bike and has_electric_ctx):
        return {
            "vehicle": "Electric Bike",
            "fuel_type": "Electric",
            "vehicle_type": "Motorcycle",
            "item_key": "electric bike",
            "factor": 0.020,
            "source": "CarbonTracker Standard"
        }
        
    # 5. bike (generic)
    if has_bike:
        if has_bicycle_ctx:
            return {
                "vehicle": "Bicycle",
                "fuel_type": "None",
                "vehicle_type": "Bicycle",
                "item_key": "bicycle",
                "factor": 0.000,
                "source": "CarbonTracker Standard"
            }
        if has_motorcycle_ctx:
            return {
                "vehicle": "Motorcycle",
                "fuel_type": "Petrol",
                "vehicle_type": "Motorcycle",
                "item_key": "motorcycle",
                "factor": 0.103,
                "source": "CarbonTracker Standard"
            }
        # default generic bike to Motorcycle
        return {
            "vehicle": "Motorcycle",
            "fuel_type": "Petrol",
            "vehicle_type": "Motorcycle",
            "item_key": "motorcycle",
            "factor": 0.103,
            "source": "CarbonTracker Standard"
        }
        
    # 6. electric scooter
    if has_electric_scooter or (has_scooter and has_electric_ctx):
        return {
            "vehicle": "Electric Scooter",
            "fuel_type": "Electric",
            "vehicle_type": "Scooter",
            "item_key": "electric scooter",
            "factor": 0.015,
            "source": "CarbonTracker Standard"
        }
        
    # 7. scooter (generic)
    if has_scooter:
        return {
            "vehicle": "Scooter",
            "fuel_type": "Petrol",
            "vehicle_type": "Scooter",
            "item_key": "petrol scooter",
            "factor": 0.075,
            "source": "CarbonTracker Standard"
        }
        
    # 8. bicycle / cycle
    if has_bicycle or has_cycle:
        return {
            "vehicle": "Bicycle",
            "fuel_type": "None",
            "vehicle_type": "Bicycle",
            "item_key": "bicycle",
            "factor": 0.000,
            "source": "CarbonTracker Standard"
        }
        
    return None

def match_transport(text: str) -> dict:
    """
    Matches a transport entity using context-aware and longest phrase matching.
    """
    cleaned = text.lower().strip()
    
    # 1. Context-aware two-wheeler check first
    two_wheeler = resolve_two_wheeler_context(cleaned)
    if two_wheeler:
        return {
            "entity": two_wheeler["vehicle"],
            "raw_match": two_wheeler["item_key"]
        }

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
