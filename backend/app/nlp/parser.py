import re
import spacy
from typing import Dict, Any, Tuple, List
from app.utils.utils import get_spelling_suggestions

# Try to load spaCy model, with silent fallback
nlp = None
try:
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        # Auto-download model if missing
        from spacy.cli import download
        download("en_core_web_sm")
        nlp = spacy.load("en_core_web_sm")
except Exception:
    nlp = None

# Flight distance estimations for common city routes (in km)
FLIGHT_ROUTES = {
    ("chennai", "delhi"): 1750,
    ("delhi", "chennai"): 1750,
    ("delhi", "mumbai"): 1150,
    ("mumbai", "delhi"): 1150,
    ("bangalore", "delhi"): 1700,
    ("delhi", "bangalore"): 1700,
    ("chennai", "bangalore"): 290,
    ("bangalore", "chennai"): 290,
    ("mumbai", "bangalore"): 850,
    ("bangalore", "mumbai"): 850,
    ("mumbai", "chennai"): 1030,
    ("chennai", "mumbai"): 1030,
    ("london", "new york"): 5570,
    ("new york", "london"): 5570,
    ("new york", "los angeles"): 3940,
    ("los angeles", "new york"): 3940,
}

# Mapping keywords to categories and canonical items
KEYWORD_MAPPINGS = {
    # --- Food ---
    "curd rice": ("food", "curd rice", "plate"),
    "curd": ("food", "curd", "kg"),
    "yogurt": ("food", "curd", "kg"),
    "biryani": ("food", "chicken biryani", "plate"),
    "chicken biryani": ("food", "chicken biryani", "plate"),
    "chicken": ("food", "chicken", "kg"),
    "beef": ("food", "beef", "kg"),
    "rice": ("food", "rice", "kg"),
    "milk": ("food", "milk", "cup"),
    "egg": ("food", "egg", "item"),
    "eggs": ("food", "egg", "item"),
    "vegetable": ("food", "vegetables", "kg"),
    "vegetables": ("food", "vegetables", "kg"),
    "veg": ("food", "vegetables", "kg"),
    "salad": ("food", "vegetables", "plate"),
    "fish": ("food", "fish", "kg"),
    "cheese": ("food", "cheese", "kg"),
    "paneer dosa": ("food", "dosa", "item"),
    "paneer": ("food", "paneer", "kg"),
    "dosa": ("food", "dosa", "item"),
    "idli": ("food", "idli", "item"),
    "idlis": ("food", "idli", "item"),
    "bread": ("food", "bread", "kg"),
    "toast": ("food", "bread", "slice"),
    
    # --- Transport ---
    "car": ("transport", "petrol car", "km"),
    "petrol car": ("transport", "petrol car", "km"),
    "diesel car": ("transport", "diesel car", "km"),
    "ev": ("transport", "ev", "km"),
    "electric car": ("transport", "ev", "km"),
    "tesla": ("transport", "ev", "km"),
    "bike": ("transport", "bike", "km"),
    "motorcycle": ("transport", "bike", "km"),
    "scooter": ("transport", "bike", "km"),
    "bus": ("transport", "bus", "km"),
    "train": ("transport", "train", "km"),
    "metro": ("transport", "metro", "km"),
    "subway": ("transport", "metro", "km"),
    "flight": ("transport", "flight", "km"),
    "plane": ("transport", "flight", "km"),
    "flew": ("transport", "flight", "km"),
    "walked": ("exercise", "walking", "km"),
    "walking": ("exercise", "walking", "km"),
    "cycle": ("exercise", "cycling", "km"),
    "cycling": ("exercise", "cycling", "km"),
    "bicycle": ("exercise", "cycling", "km"),
    "run": ("exercise", "running", "km"),
    "ran": ("exercise", "running", "km"),
    "running": ("exercise", "running", "km"),
    "jog": ("exercise", "jogging", "km"),
    "jogged": ("exercise", "jogging", "km"),
    "jogging": ("exercise", "jogging", "km"),
    "swim": ("exercise", "swimming", "km"),
    "swimming": ("exercise", "swimming", "km"),
    "workout": ("exercise", "exercise", "item"),
    "exercise": ("exercise", "exercise", "item"),
    "air_conditioner": ("appliances", "ac", "hours"),
    "vegetarian_food": ("food", "vegetables", "kg"),
    
    # --- Appliances ---
    "ac": ("appliances", "ac", "hours"),
    "air conditioner": ("appliances", "ac", "hours"),
    "cooling": ("appliances", "ac", "hours"),
    "fan": ("appliances", "fan", "hours"),
    "fridge": ("appliances", "refrigerator", "hours"),
    "refrigerator": ("appliances", "refrigerator", "hours"),
    "laptop": ("appliances", "laptop", "hours"),
    "computer": ("appliances", "laptop", "hours"),
    "macbook": ("appliances", "laptop", "hours"),
    "tv": ("appliances", "tv", "hours"),
    "television": ("appliances", "tv", "hours"),
    "washing machine": ("appliances", "washing machine", "hours"),
    "washer": ("appliances", "washing machine", "hours"),
    "water heater": ("appliances", "water heater", "hours"),
    "geyser": ("appliances", "water heater", "hours"),
    "light": ("appliances", "lights", "hours"),
    "lights": ("appliances", "lights", "hours"),
    "bulb": ("appliances", "lights", "hours"),
    
    # --- Waste ---
    "organic waste": ("waste", "organic waste", "kg"),
    "food waste": ("waste", "organic waste", "kg"),
    "garbage": ("waste", "organic waste", "kg"),
    "plastic": ("waste", "plastic waste", "kg"),
    "paper": ("waste", "paper waste", "kg"),
    "recycling": ("waste", "recycling", "kg"),
    "recycled": ("waste", "recycling", "kg"),
    
    # --- Water ---
    "water": ("water", "tap water", "L"),
    "shower": ("water", "tap water", "L"),
    "tap water": ("water", "tap water", "L"),
    
    # --- Shopping ---
    "shirt": ("shopping", "clothing", "item"),
    "t-shirt": ("shopping", "clothing", "item"),
    "jeans": ("shopping", "clothing", "item"),
    "clothes": ("shopping", "clothing", "item"),
    "shoes": ("shopping", "shoes", "item"),
    "phone": ("shopping", "electronics", "item"),
    "smartphone": ("shopping", "electronics", "item"),
    "iphone": ("shopping", "electronics", "item"),
    "tablet": ("shopping", "electronics", "item"),
}

# Standard text numbers to float conversion
TEXT_NUMBERS = {
    "a": 1.0, "an": 1.0, "one": 1.0, "two": 2.0, "three": 3.0, "four": 4.0, "five": 5.0,
    "six": 6.0, "seven": 7.0, "eight": 8.0, "nine": 9.0, "ten": 10.0,
    "twice": 2.0, "thrice": 3.0, "double": 2.0
}

def preprocess_text(text: str) -> str:
    """
    Cleans up input string for parsing.
    """
    from app.nlp.parser_synonyms import map_synonyms
    text = map_synonyms(text)
    text = text.lower().strip()
    text = re.sub(r'\b(kms|kilometres|kilometer|kilometers)\b', 'km', text)
    text = re.sub(r'\b(miles|mile)\b', 'mile', text)
    text = re.sub(r'\b(hours|hour|hrs|hr)\b', 'hours', text)
    text = re.sub(r'\b(liters|liter|litres|litre|lts|l)\b', 'l', text)
    text = re.sub(r'\b(grams|gram|g)\b', 'g', text)
    text = re.sub(r'\b(kilograms|kilogram|kg|kgs)\b', 'kg', text)
    text = re.sub(r'\b(plates|plate)\b', 'plate', text)
    text = re.sub(r'\b(bowls|bowl)\b', 'bowl', text)
    text = re.sub(r'\b(cups|cup)\b', 'cup', text)
    text = re.sub(r'\b(servings|serving)\b', 'serving', text)
    text = re.sub(r'\b(glasses|glass)\b', 'glass', text)
    return text

def parse_activity_text(text: str) -> Dict[str, Any]:
    """
    Parses natural language input to identify quantity, unit, category, and canonical item.
    Fuses direct keyword checks, spelling suggestions, and embedding semantic matching.
    """
    cleaned = preprocess_text(text)
    
    # Initial defaults
    category = None
    item = None
    quantity = 1.0
    unit = "item"
    confidence = 0.40
    ambiguity = 0.60
    suggestions = []
    
    # 1. Extract Quantity & Unit using Regex
    num_pattern = r'(\d+(?:\.\d+)?)\s*([a-zA-Z]+)?'
    matches = re.findall(num_pattern, cleaned)
    
    parsed_quantity = None
    parsed_unit = None
    
    if matches:
        val_str, unit_candidate = matches[0]
        parsed_quantity = float(val_str)
        if unit_candidate:
            parsed_unit = unit_candidate.lower()
            
    if parsed_quantity is None:
        for word in cleaned.split():
            if word in TEXT_NUMBERS:
                parsed_quantity = TEXT_NUMBERS[word]
                if word in ["twice", "thrice"]:
                    parsed_unit = "times"
                break
                
    if parsed_quantity is not None:
        quantity = parsed_quantity
    if parsed_unit is not None:
        unit = parsed_unit

    # Standardize units
    if unit in ["miles", "mile", "mi"]:
        unit = "miles"
    elif unit in ["plates", "plate"]:
        unit = "plate"
    elif unit in ["bowls", "bowl"]:
        unit = "bowl"
    elif unit in ["cups", "cup"]:
        unit = "cup"
    elif unit in ["servings", "serving"]:
        unit = "serving"
    elif unit in ["hours", "hour", "hrs", "hr"]:
        unit = "hours"
    elif unit in ["g", "grams", "gram"]:
        unit = "g"
    elif unit in ["kg", "kilograms", "kilogram"]:
        unit = "kg"
    elif unit in ["l", "liter", "liters", "litre", "litres"]:
        unit = "L"

    # 2. Extract Category and Item using intent priority routing
    #
    # Priority 1: Exercise Activities
    # ----------------------------------------------------
    exercise_keywords = [
        "running", "walking", "jogging", "cycling", "swimming", "workout", "exercise", "swim", "run", "ran", "walk", "walked", "cycle", "cycled", "bicycle"
    ]
    is_exercise = False
    matched_ex_kw = None
    for kw in exercise_keywords:
        if re.search(r'\b' + re.escape(kw) + r'\b', cleaned):
            is_exercise = True
            matched_ex_kw = kw
            break
            
    if is_exercise:
        category = "exercise"
        confidence = 1.0
        ambiguity = 0.0
        
        # Map to canonical exercise item
        if matched_ex_kw in ["run", "ran", "running"]:
            item = "running"
        elif matched_ex_kw in ["walk", "walked", "walking"]:
            item = "walking"
        elif matched_ex_kw in ["jog", "jogging"]:
            item = "jogging"
        elif matched_ex_kw in ["cycle", "cycled", "cycling", "bicycle"]:
            item = "cycling"
        elif matched_ex_kw in ["swim", "swimming"]:
            item = "swimming"
        else:
            item = "exercise"
            
        # Default to km if no distance unit found
        if unit not in ["km", "miles"]:
            unit = "km"

    # Priority 2: Transport Activities
    # ----------------------------------------------------
    transport_keywords = [
        "car", "motorcycle", "bike", "bus", "train", "flight", "auto", "taxi",
        "cab", "truck", "van", "drove", "rode", "travelled by", "commuted by",
        "petrol car", "diesel car", "electric car", "travelled"
    ]
    matched_keyword = None
    if not category:
        is_transport = False
        for kw in transport_keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', cleaned):
                is_transport = True
                break
                
        if is_transport:
            for kw, (cat, canonical_item, def_unit) in KEYWORD_MAPPINGS.items():
                if cat == "transport" and re.search(r'\b' + re.escape(kw) + r'\b', cleaned):
                    category = "transport"
                    item = canonical_item
                    unit = def_unit if parsed_unit is None else unit
                    matched_keyword = kw
                    confidence = 0.95
                    ambiguity = 0.05
                    break
            
            # Constraints: if no direct keyword matched, try semantic but only if category is transport
            if not matched_keyword:
                try:
                    from app.ai.semantic.semantic import find_semantic_match, get_semantic_confidence
                    from app.utils.circuit_breaker import breakers
                    sem_match = breakers["embeddings"].call(find_semantic_match, cleaned)
                    if sem_match:
                        matched_keyword, similarity = sem_match
                        cat, canonical_item, def_unit = KEYWORD_MAPPINGS[matched_keyword]
                        if cat == "transport":
                            category = "transport"
                            item = canonical_item
                            unit = def_unit if parsed_unit is None else unit
                            confidence, ambiguity = get_semantic_confidence(cleaned, matched_keyword, similarity)
                except Exception:
                    pass
            
            # Default fallback for transport if no mapping found but transport words present
            if not category:
                category = "transport"
                item = "petrol car"
                unit = "km"
                confidence = 0.70
                ambiguity = 0.30

    # Priority 3: Food Activities
    # ----------------------------------------------------
    # Pass A: Use the structured food knowledge base (longest-phrase-first).
    # This correctly identifies full dish names like "Chicken Biriyani" before
    # falling back to bare ingredient words like "chicken" or "rice".
    if not category:
        from app.nlp.food_emission_factors import lookup_food, get_ingredient_fallback
        food_hit = lookup_food(cleaned)
        if food_hit is None:
            # Rule 4: ingredient fallback (e.g. "Chicken Pasta" → Chicken category)
            food_hit = get_ingredient_fallback(cleaned)
        if food_hit:
            category = "food"
            item = food_hit["name"]
            unit = food_hit["unit"] if parsed_unit is None else unit
            # Store co2_kg for the engine to use directly
            _food_co2_kg = food_hit["co2_kg"]
            confidence = 0.97
            ambiguity = 0.03
        else:
            _food_co2_kg = None

    # Pass B: Legacy KEYWORD_MAPPINGS fallback for any remaining food keywords
    # not covered by the new database (e.g. generic "rice", "milk", "bread").
    if not category:
        _food_co2_kg = None
        for kw, (cat, canonical_item, def_unit) in KEYWORD_MAPPINGS.items():
            if cat == "food" and re.search(r'\b' + re.escape(kw) + r'\b', cleaned):
                category = "food"
                item = canonical_item
                unit = def_unit if parsed_unit is None else unit
                matched_keyword = kw
                confidence = 0.95
                ambiguity = 0.05
                break
    else:
        if category == "food" and "_food_co2_kg" not in dir():
            _food_co2_kg = None

    # Priority 4: Energy/Appliance Activities
    # ----------------------------------------------------
    if not category:
        for kw, (cat, canonical_item, def_unit) in KEYWORD_MAPPINGS.items():
            if cat == "appliances" and re.search(r'\b' + re.escape(kw) + r'\b', cleaned):
                category = "appliances"
                item = canonical_item
                unit = def_unit if parsed_unit is None else unit
                matched_keyword = kw
                confidence = 0.95
                ambiguity = 0.05
                break

    # Priority 5: Shopping Activities
    # ----------------------------------------------------
    if not category:
        for kw, (cat, canonical_item, def_unit) in KEYWORD_MAPPINGS.items():
            if cat == "shopping" and re.search(r'\b' + re.escape(kw) + r'\b', cleaned):
                category = "shopping"
                item = canonical_item
                unit = def_unit if parsed_unit is None else unit
                matched_keyword = kw
                confidence = 0.95
                ambiguity = 0.05
                break

    # Priority 6: Waste Activities
    # ----------------------------------------------------
    if not category:
        for kw, (cat, canonical_item, def_unit) in KEYWORD_MAPPINGS.items():
            if cat == "waste" and re.search(r'\b' + re.escape(kw) + r'\b', cleaned):
                category = "waste"
                item = canonical_item
                unit = def_unit if parsed_unit is None else unit
                matched_keyword = kw
                confidence = 0.95
                ambiguity = 0.05
                break

    # Priority 7: Water Activities
    # ----------------------------------------------------
    if not category:
        for kw, (cat, canonical_item, def_unit) in KEYWORD_MAPPINGS.items():
            if cat == "water" and re.search(r'\b' + re.escape(kw) + r'\b', cleaned):
                category = "water"
                item = canonical_item
                unit = def_unit if parsed_unit is None else unit
                matched_keyword = kw
                confidence = 0.95
                ambiguity = 0.05
                break

    # Fallback: Semantic matching across non-transport categories
    if not category:
        try:
            from app.ai.semantic.semantic import find_semantic_match, get_semantic_confidence
            from app.utils.circuit_breaker import breakers
            sem_match = breakers["embeddings"].call(find_semantic_match, cleaned)
            if sem_match:
                matched_keyword, similarity = sem_match
                cat, canonical_item, def_unit = KEYWORD_MAPPINGS[matched_keyword]
                if cat != "transport":
                    category = cat
                    item = canonical_item
                    unit = def_unit if parsed_unit is None else unit
                    confidence, ambiguity = get_semantic_confidence(cleaned, matched_keyword, similarity)
        except Exception:
            pass

    # Final fallback if still nothing matches
    if not category:
        category = "lifestyle"
        item = "general activity"
        unit = "item" if parsed_unit is None else unit
        confidence = 0.30
        ambiguity = 0.70
        
        # Scrape words from input excluding standard filler/number words
        fillers = {"for", "by", "used", "ate", "travelled", "watched", "had", "drank", "consumed", "logged", "plate", "bowl", "cup", "serving", "g", "kg", "ml", "l", "km", "hours", "miles", "times"}
        words_to_check = [
            w for w in cleaned.split() 
            if w not in TEXT_NUMBERS and not re.match(r'^\d', w) and w not in fillers and len(w) > 2
        ]
        
        suggested_keys = []
        for word in words_to_check:
            opts = get_spelling_suggestions(word, list(KEYWORD_MAPPINGS.keys()), max_suggestions=2, threshold=2)
            suggested_keys.extend(opts)
            
        suggestions_list = []
        for key in suggested_keys:
            _, item_name, _ = KEYWORD_MAPPINGS[key]
            if item_name not in suggestions_list:
                suggestions_list.append(item_name)
        suggestions = suggestions_list[:3]

    # Post-processing calculations for special cases
    #
    # 3. Special Case: Flights / Air Travel Route Estimator
    if category == "transport" and item == "flight":
        flight_pattern = r'flight\s+(?:from\s+)?([a-zA-Z\s]+)\s+to\s+([a-zA-Z\s]+)'
        route_match = re.search(flight_pattern, cleaned)
        if route_match:
            city_a = route_match.group(1).strip()
            city_b = route_match.group(2).strip()
            
            route_key = (city_a, city_b)
            reversed_key = (city_b, city_a)
            
            distance = None
            if route_key in FLIGHT_ROUTES:
                distance = FLIGHT_ROUTES[route_key]
            elif reversed_key in FLIGHT_ROUTES:
                distance = FLIGHT_ROUTES[reversed_key]
                
            if distance:
                quantity = distance
                unit = "km"
                item = f"flight ({city_a.title()} -> {city_b.title()})"
                confidence = 0.98
            else:
                quantity = 800.0
                unit = "km"
                item = f"flight ({city_a.title()} -> {city_b.title()})"
                confidence = 0.80
                
    # 4. Special Case: Appliance duration calculation
    if category == "appliances":
        if unit in ["times", "twice", "time", "runs", "run"]:
            unit = "hours"
            
    # 5. Special Case: Shower time to water quantity
    if item == "tap water" and "shower" in cleaned:
        min_match = re.search(r'(\d+)\s*(?:minute|minutes|min|mins)', cleaned)
        if min_match:
            mins = float(min_match.group(1))
            quantity = mins * 9.0
            unit = "L"
            item = "shower"
            confidence = 0.95
        else:
            quantity = 72.0
            unit = "L"
            item = "shower"
            confidence = 0.85
            
    spacy_entities = []
    if nlp:
        doc = nlp(text)
        for ent in doc.ents:
            spacy_entities.append({
                "text": ent.text,
                "label": ent.label_
            })
            
    try:
        from app.ai.observability.observability import track_confidence
        track_confidence(confidence)
    except Exception:
        pass

    # Step 8 low-confidence fallback to "Needs Clarification"
    if confidence < 0.50:
        category = "lifestyle"
        item = "Needs Clarification"
        quantity = 0.0
        unit = "unit"
        ambiguity = round(1.0 - confidence, 2)
        suggestions = []
        
    return {
        "category": category,
        "item": item,
        "quantity": quantity,
        "unit": unit,
        "confidence": round(confidence, 2),
        "ambiguity": round(ambiguity, 2),
        "suggestions": suggestions,
        "original_text": text,
        "spacy_entities": spacy_entities,
        # Pre-calculated food CO₂ value from food_emission_factors.py (None for non-food)
        "food_co2_kg": locals().get("_food_co2_kg", None),
    }

def parse_compound_activity(text: str) -> List[Dict[str, Any]]:
    """
    Splits compound natural language strings (e.g. using 'and', 'then', 'as well as', 'along with')
    into multiple individual activity dictionaries.
    """
    # Regex splitting on: and also, as well as, along with, then, plus, and, commas
    parts = re.split(
        r'\s+and\s+also\s+|\s+as\s+well\s+as\s+|\s+along\s+with\s+|\s+then\s+|\s+plus\s+|\s+and\s+|,\s*',
        text,
        flags=re.IGNORECASE
    )
    results = []
    
    for part in parts:
        part_clean = part.strip()
        if not part_clean:
            continue
            
        # Parse individual part
        parsed = parse_activity_text(part_clean)
        
        # Keep if it matched a valid category or keywords (not generic fallback)
        # Or if it's the only part
        if len(parts) == 1 or parsed["category"] != "lifestyle" or parsed["confidence"] > 0.40:
            results.append(parsed)
            
    if not results:
        # Emergency single fallback
        results.append(parse_activity_text(text))
        
    return results
