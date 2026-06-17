import re
import spacy
from typing import Dict, Any, Tuple, List
from app.utils.utils import get_spelling_suggestions

# Try to load spaCy model, with silent fallback (lazy loaded)
nlp = None
_spacy_loaded = False

def get_nlp():
    from app.nlp.spacy_service import get_spacy_nlp
    return get_spacy_nlp()

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

# ---------------------------------------------------------------------------
# EXERCISE HARD BLOCK
# ---------------------------------------------------------------------------
# CRITICAL SAFETY RULE:
# If ANY word in the user's input appears in this set, the parser MUST
# classify the activity as Exercise and MUST NOT execute the food parser.
#
# This is a module-level guard — it runs before any lazy import, DB call,
# or keyword-mapping loop. Adding a keyword here is the single source of
# truth for exercise-or-nothing classification.
#
# Rule: Exercise Intent > 0  →  Food parser skipped entirely.
# Rule: Unknown activity     →  Return "unknown", never default to food.
# ---------------------------------------------------------------------------
EXERCISE_HARD_BLOCK: frozenset = frozenset({
    # Distance activities
    "running", "run", "ran",
    "walking", "walk", "walked",
    "jogging", "jog", "jogged",
    "cycling", "cycle", "cycled", "bicycle",
    "swimming", "swim", "swam",
    "trekking", "trek", "trekked",
    "hiking", "hike", "hiked",
    # Mind-body & gym (CRITICAL — these caused the curd bug)
    "yoga",
    "workout",
    "gym",
    "exercise",
    "exercised",
    "fitness",
    "meditation",
    "meditated",
    "stretching",
    "stretched",
    "pilates",
    "zumba",
    "aerobics",
    "crossfit",
    "calisthenics",
    # Compound (matched as substring)
    "surya namaskar",
    "yoga session",
    "gym session",
    "morning walk",
    "evening walk",
    "morning run",
    "worked out",
})

def _has_exercise_keyword(text: str) -> str | None:
    """
    Scans lowercased text for any word/phrase in EXERCISE_HARD_BLOCK.
    Returns the matched keyword, or None if no exercise found.
    Compound phrases are checked first (longest-match wins).
    """
    text_lower = text.lower()
    # Check compound phrases first
    for phrase in sorted(EXERCISE_HARD_BLOCK, key=len, reverse=True):
        if ' ' in phrase:
            if phrase in text_lower:
                return phrase
    # Then individual words with word-boundary check
    for kw in sorted(EXERCISE_HARD_BLOCK, key=len, reverse=True):
        if ' ' not in kw:
            if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                return kw
    return None


def preprocess_text(text: str) -> str:
    """
    Cleans up input string for parsing.
    """
    from app.nlp.entity_engine import normalize_units_in_text
    text = normalize_units_in_text(text)
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

    Pipeline
    --------
    -1. spaCy enhancement layer (PhraseMatcher)
    0. Intent detection  — verb-first (shopping/energy/transport/food/exercise)
    1. Exercise          — zero-emission human activity
    2. Shopping intent   — bought/purchased/ordered → shopping category
    3. Transport intent  — city-route lookup → distance + vehicle factor
    4. Food intent       — food knowledge base (longest-phrase-first)
    5. Energy intent     — wattage-based or appliance-table calculation
    6. Appliance/Energy  — keyword fallback
    7. Legacy categories — waste, water, shopping fallback
    8. Semantic matching — last resort
    """
    try:
        from app.nlp.spacy_parser import parse_spacy
        spacy_result = parse_spacy(text)
        if spacy_result is not None:
            return spacy_result
    except Exception:
        pass

    from app.nlp.intent_router import (
        detect_intent, detect_wattage, compute_wattage_emission,
        lookup_shopping_emission, lookup_city_route, detect_vehicle,
        VEHICLE_EMISSION_FACTORS,
    )
    from app.nlp.intent_engine import detect_intent as detect_intent_engine

    cleaned = preprocess_text(text)

    # Initialize single spaCy document for this request
    nlp_model = get_nlp()
    doc = nlp_model(cleaned) if nlp_model else None

    # Initial defaults
    category   = None
    item       = None
    quantity   = 1.0
    unit       = "item"
    confidence = 0.40
    ambiguity  = 0.60
    suggestions: List = []
    _food_co2_kg:   float | None = None
    _shopping_co2:  float | None = None
    _wattage_result: dict | None = None  # pre-computed wattage emission

    # ── Step 0: Detect user intent from verbs ─────────────────────────────
    intent_res = detect_intent_engine(cleaned)
    intent_val = intent_res.intent
    exercise_score = intent_res.scores.get("exercise", 0.0)
    skip_food_parsing = (exercise_score > 0)
    intent = intent_val if intent_val != "unknown" else None

    # ── Step 1: Extract Quantity & Unit ───────────────────────────────────
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
        tokens = [token.text for token in doc] if doc else cleaned.split()
        for word in tokens:
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

    # ── Priority 0-A: Exercise intent (always zero-emission) ──────────────
    # IMPORTANT: This list must be checked BEFORE any food/appliance lookup.
    # Yoga, meditation, stretching etc. must NEVER fall through to food.
    EXERCISE_DISTANCE_KWS = [
        "run", "ran", "running",
        "walk", "walked", "walking",
        "jog", "jogged", "jogging",
        "cycle", "cycled", "cycling", "bicycle",
        "swim", "swam", "swimming",
        "trek", "trekked", "trekking",
        "hike", "hiked", "hiking",
    ]
    EXERCISE_DURATION_KWS = [
        "yoga", "yoga session",
        "surya namaskar",
        "meditation", "meditated",
        "stretching",
        "gym", "gym session",
        "workout", "worked out",
        "exercise", "exercised",
        "fitness",
        "pilates",
        "zumba",
        "aerobics",
        "crossfit",
        "calisthenics",
    ]
    ALL_EXERCISE_KWS = EXERCISE_DISTANCE_KWS + EXERCISE_DURATION_KWS

    matched_ex_kw = None
    # Try multi-word phrases first (longest match)
    for kw in sorted(ALL_EXERCISE_KWS, key=len, reverse=True):
        if re.search(r'\b' + re.escape(kw) + r'\b', cleaned):
            matched_ex_kw = kw
            break

    if matched_ex_kw or intent == "exercise":
        category   = "exercise"
        confidence = 1.0
        ambiguity  = 0.0
        # Map keyword → canonical item name
        if matched_ex_kw in ["run", "ran", "running"]:
            item = "running"
            if unit not in ["km", "miles"]: unit = "km"
        elif matched_ex_kw in ["walk", "walked", "walking"]:
            item = "walking"
            if unit not in ["km", "miles"]: unit = "km"
        elif matched_ex_kw in ["jog", "jogged", "jogging"]:
            item = "jogging"
            if unit not in ["km", "miles"]: unit = "km"
        elif matched_ex_kw in ["cycle", "cycled", "cycling", "bicycle"]:
            item = "cycling"
            if unit not in ["km", "miles"]: unit = "km"
        elif matched_ex_kw in ["swim", "swam", "swimming"]:
            item = "swimming"
            if unit not in ["km", "miles"]: unit = "km"
        elif matched_ex_kw in ["trek", "trekked", "trekking"]:
            item = "trekking"
            if unit not in ["km", "miles"]: unit = "km"
        elif matched_ex_kw in ["hike", "hiked", "hiking"]:
            item = "hiking"
            if unit not in ["km", "miles"]: unit = "km"
        elif matched_ex_kw in ["yoga", "yoga session"]:
            item = "yoga"
            if unit not in ["hours", "minutes"]: unit = "hours"
        elif matched_ex_kw == "surya namaskar":
            item = "surya namaskar"
            if unit not in ["hours", "minutes", "rounds"]: unit = "rounds"
        elif matched_ex_kw in ["meditation", "meditated"]:
            item = "meditation"
            if unit not in ["hours", "minutes"]: unit = "hours"
        elif matched_ex_kw == "stretching":
            item = "stretching"
            if unit not in ["hours", "minutes"]: unit = "hours"
        elif matched_ex_kw in ["gym", "gym session"]:
            item = "gym"
            if unit not in ["hours", "minutes"]: unit = "hours"
        elif matched_ex_kw in ["workout", "worked out"]:
            item = "workout"
            if unit not in ["hours", "minutes"]: unit = "hours"
        elif matched_ex_kw in ["exercise", "exercised"]:
            item = "exercise"
            if unit not in ["hours", "minutes", "km", "miles"]: unit = "hours"
        elif matched_ex_kw == "pilates":
            item = "pilates"
            if unit not in ["hours", "minutes"]: unit = "hours"
        elif matched_ex_kw == "zumba":
            item = "zumba"
            if unit not in ["hours", "minutes"]: unit = "hours"
        elif matched_ex_kw in ["fitness", "aerobics", "crossfit", "calisthenics"]:
            item = matched_ex_kw
            if unit not in ["hours", "minutes"]: unit = "hours"
        else:
            # intent == "exercise" but no specific keyword matched
            item = "exercise"
            if unit not in ["km", "miles", "hours", "minutes"]: unit = "hours"

    # ── Priority 0-B: Shopping Intent ─────────────────────────────────────
    # "I bought a laptop" → shopping regardless of noun
    if not category and intent == "shopping":
        hit = lookup_shopping_emission(cleaned)
        if hit:
            item_name, co2_val = hit
            category       = "shopping"
            if item_name in ["shirt", "t-shirt", "jeans", "dress", "jacket", "coat", "clothing", "bag", "backpack"]:
                item = "clothing"
            elif item_name in ["shoes", "sneakers"]:
                item = "shoes"
            elif item_name in ["phone", "smartphone", "iphone", "tablet", "electronics"]:
                item = "electronics"
            else:
                item = item_name
            unit           = "item"
            _shopping_co2  = co2_val
            confidence     = 0.97
            ambiguity      = 0.03
        else:
            # Generic shopping item — use keyword fallback below
            category   = "shopping"
            item       = "clothing"   # placeholder, overridden by keyword below
            unit       = "item"
            confidence = 0.80
            ambiguity  = 0.20
            # Try to extract noun from KEYWORD_MAPPINGS
            for kw, (cat, canonical_item, def_unit) in KEYWORD_MAPPINGS.items():
                if cat == "shopping" and re.search(r'\b' + re.escape(kw) + r'\b', cleaned):
                    item = canonical_item
                    unit = def_unit if parsed_unit is None else unit
                    confidence = 0.90
                    break

    # ── Priority 0-C: Transport Intent + City Route ───────────────────────
    # "I went from Chennai to Madurai by electric train" → transport
    if not category and intent == "transport":
        route = lookup_city_route(cleaned, doc=doc)
        vehicle = detect_vehicle(cleaned)
        factor = VEHICLE_EMISSION_FACTORS.get(vehicle, 0.192)

        if route:
            city_a, city_b, dist_km = route
            emissions_val = dist_km * factor
            category  = "transport"
            item      = f"{vehicle} ({city_a.title()} → {city_b.title()})"
            quantity  = float(dist_km)
            unit      = "km"
            confidence = 0.98
            ambiguity  = 0.02
            # Store pre-computed result in metadata hint
            _wattage_result = {
                "calculation_type": "city_route",
                "city_from": city_a.title(),
                "city_to": city_b.title(),
                "distance_km": dist_km,
                "vehicle": vehicle,
                "emission_factor": factor,
                "total_emissions_kg": round(emissions_val, 4),
            }
        else:
            # Normal transport without a city route
            for kw, (cat, canonical_item, def_unit) in KEYWORD_MAPPINGS.items():
                if cat == "transport" and re.search(r'\b' + re.escape(kw) + r'\b', cleaned):
                    category  = "transport"
                    item      = canonical_item
                    unit      = def_unit if parsed_unit is None else unit
                    confidence = 0.95
                    ambiguity  = 0.05
                    break
            if not category:
                category  = "transport"
                item      = vehicle
                unit      = "km"
                confidence = 0.85
                ambiguity  = 0.15

    # ── Priority 0-D: Energy Intent + Wattage ─────────────────────────────
    # "charged my laptop for 1 hour using a 60W charger" → energy
    if not category and intent == "energy":
        watts = detect_wattage(cleaned)
        hours_val = quantity if unit in ["hours", "times", "twice", "time", "runs", "run"] else 1.0
        appliance_item = "laptop charging"

        # Identify the appliance noun
        for kw, (cat, canonical_item, def_unit) in KEYWORD_MAPPINGS.items():
            if cat == "appliances" and re.search(r'\b' + re.escape(kw) + r'\b', cleaned):
                appliance_item = canonical_item
                break

        category  = "appliances"
        item      = appliance_item
        unit      = "hours"
        confidence = 0.96
        ambiguity  = 0.04

        if watts is not None:
            co2_val, meta = compute_wattage_emission(watts, hours_val)
            _wattage_result = meta
            quantity = hours_val
        else:
            quantity = hours_val

    # ── Priority 1: Food Activities ───────────────────────────────────────
    if not category and not skip_food_parsing:
        from app.nlp.food_emission_factors import lookup_food, get_ingredient_fallback
        food_hit = lookup_food(cleaned)
        if food_hit is None:
            food_hit = get_ingredient_fallback(cleaned)
        if food_hit:
            category     = "food"
            item         = food_hit["name"]
            unit         = food_hit["unit"] if parsed_unit is None else unit
            _food_co2_kg = food_hit["co2_kg"]
            confidence   = 0.97
            ambiguity    = 0.03

    # ── Priority 2: Legacy Transport (no intent verb, but transport noun) ──
    if not category:
        transport_keywords = [
            "car", "motorcycle", "bike", "bus", "train", "flight", "auto", "taxi",
            "cab", "truck", "van", "drove", "rode", "petrol car", "diesel car",
            "electric car", "electric train",
        ]
        is_transport = any(
            re.search(r'\b' + re.escape(kw) + r'\b', cleaned)
            for kw in transport_keywords
        )
        if is_transport:
            route = lookup_city_route(cleaned, doc=doc)
            if route:
                city_a, city_b, dist_km = route
                vehicle   = detect_vehicle(cleaned)
                factor    = VEHICLE_EMISSION_FACTORS.get(vehicle, 0.192)
                category  = "transport"
                item      = f"{vehicle} ({city_a.title()} → {city_b.title()})"
                quantity  = float(dist_km)
                unit      = "km"
                confidence = 0.97
                ambiguity  = 0.03
                _wattage_result = {
                    "calculation_type": "city_route",
                    "city_from": city_a.title(),
                    "city_to": city_b.title(),
                    "distance_km": dist_km,
                    "vehicle": vehicle,
                    "emission_factor": factor,
                    "total_emissions_kg": round(dist_km * factor, 4),
                }
            else:
                matched_keyword = None
                for kw, (cat, canonical_item, def_unit) in KEYWORD_MAPPINGS.items():
                    if cat == "transport" and re.search(r'\b' + re.escape(kw) + r'\b', cleaned):
                        category       = "transport"
                        item           = canonical_item
                        unit           = def_unit if parsed_unit is None else unit
                        matched_keyword = kw
                        confidence     = 0.95
                        ambiguity      = 0.05
                        break
                if not category:
                    category  = "transport"
                    item      = "petrol car"
                    unit      = "km"
                    confidence = 0.70
                    ambiguity  = 0.30

    # ── Priority 3: Legacy Food fallback (KEYWORD_MAPPINGS) ───────────────
    if not category and not skip_food_parsing:
        for kw, (cat, canonical_item, def_unit) in KEYWORD_MAPPINGS.items():
            if cat == "food" and re.search(r'\b' + re.escape(kw) + r'\b', cleaned):
                category  = "food"
                item      = canonical_item
                unit      = def_unit if parsed_unit is None else unit
                confidence = 0.95
                ambiguity  = 0.05
                break

    # ── Priority 4: Appliances / Energy ───────────────────────────────────
    if not category:
        for kw, (cat, canonical_item, def_unit) in KEYWORD_MAPPINGS.items():
            if cat == "appliances" and re.search(r'\b' + re.escape(kw) + r'\b', cleaned):
                category  = "appliances"
                item      = canonical_item
                unit      = def_unit if parsed_unit is None else unit
                confidence = 0.95
                ambiguity  = 0.05
                break

    # ── Priority 5: Shopping (noun fallback, no intent verb) ──────────────
    if not category:
        for kw, (cat, canonical_item, def_unit) in KEYWORD_MAPPINGS.items():
            if cat == "shopping" and re.search(r'\b' + re.escape(kw) + r'\b', cleaned):
                category  = "shopping"
                item      = canonical_item
                unit      = def_unit if parsed_unit is None else unit
                confidence = 0.95
                ambiguity  = 0.05
                break

    # ── Priority 6: Waste ─────────────────────────────────────────────────
    if not category:
        for kw, (cat, canonical_item, def_unit) in KEYWORD_MAPPINGS.items():
            if cat == "waste" and re.search(r'\b' + re.escape(kw) + r'\b', cleaned):
                category  = "waste"
                item      = canonical_item
                unit      = def_unit if parsed_unit is None else unit
                confidence = 0.95
                ambiguity  = 0.05
                break

    # ── Priority 7: Water ─────────────────────────────────────────────────
    if not category:
        for kw, (cat, canonical_item, def_unit) in KEYWORD_MAPPINGS.items():
            if cat == "water" and re.search(r'\b' + re.escape(kw) + r'\b', cleaned):
                category  = "water"
                item      = canonical_item
                unit      = def_unit if parsed_unit is None else unit
                confidence = 0.95
                ambiguity  = 0.05
                break

    # ── Semantic matching fallback ─────────────────────────────────────────
    if not category:
        try:
            from app.ai.semantic.semantic import find_semantic_match, get_semantic_confidence
            from app.utils.circuit_breaker import breakers
            sem_match = breakers["embeddings"].call(find_semantic_match, cleaned)
            if sem_match:
                matched_keyword, similarity = sem_match
                cat, canonical_item, def_unit = KEYWORD_MAPPINGS[matched_keyword]
                if cat != "transport":
                    if not (skip_food_parsing and cat == "food"):
                        category  = cat
                        item      = canonical_item
                        unit      = def_unit if parsed_unit is None else unit
                        confidence, ambiguity = get_semantic_confidence(cleaned, matched_keyword, similarity)
        except Exception:
            pass

    # ── Final fallback ─────────────────────────────────────────────────────
    if not category:
        category  = "lifestyle"
        item      = "general activity"
        unit      = "item" if parsed_unit is None else unit
        confidence = 0.30
        ambiguity  = 0.70
        fillers = {
            "for", "by", "used", "ate", "travelled", "watched", "had", "drank",
            "consumed", "logged", "plate", "bowl", "cup", "serving",
            "g", "kg", "ml", "l", "km", "hours", "miles", "times",
        }
        nlp_model = get_nlp()
        tokens = [t.text for t in nlp_model(cleaned)] if nlp_model else cleaned.split()
        words_to_check = [
            w for w in tokens
            if w not in TEXT_NUMBERS and not re.match(r'^\d', w)
            and w not in fillers and len(w) > 2
        ]
        suggested_keys = []
        for word in words_to_check:
            opts = get_spelling_suggestions(word, list(KEYWORD_MAPPINGS.keys()), max_suggestions=2, threshold=2)
            suggested_keys.extend(opts)
        suggestions_list = []
        for key in suggested_keys:
            cat, item_name, _ = KEYWORD_MAPPINGS[key]
            if skip_food_parsing and cat == "food":
                continue
            if item_name not in suggestions_list:
                suggestions_list.append(item_name)
        suggestions = suggestions_list[:3]

    # ── Post-processing: Flight route estimator ────────────────────────────
    if category == "transport" and item == "flight":
        flight_pattern = r'flight\s+(?:from\s+)?([a-zA-Z\s]+)\s+to\s+([a-zA-Z\s]+)'
        route_match = re.search(flight_pattern, cleaned)
        if route_match:
            city_a = route_match.group(1).strip()
            city_b = route_match.group(2).strip()
            from app.nlp.intent_router import CITY_DISTANCES
            route_key = (city_a, city_b)
            reversed_key = (city_b, city_a)
            distance = CITY_DISTANCES.get(route_key) or CITY_DISTANCES.get(reversed_key)
            if distance:
                quantity = float(distance)
                unit = "km"
                item = f"flight ({city_a.title()} → {city_b.title()})"
                confidence = 0.98
            else:
                quantity = 800.0
                unit = "km"
                item = f"flight ({city_a.title()} → {city_b.title()})"
                confidence = 0.80

    # ── Post-processing: Appliance duration fix ───────────────────────────
    if category == "appliances":
        if unit in ["times", "twice", "time", "runs", "run"]:
            unit = "hours"

    # ── Post-processing: Shower → water quantity ──────────────────────────
    if item == "tap water" and "shower" in cleaned:
        min_match = re.search(r'(\d+)\s*(?:minute|minutes|min|mins)', cleaned)
        if min_match:
            quantity = float(min_match.group(1)) * 9.0
            unit = "L"
            item = "shower"
            confidence = 0.95
        else:
            quantity = 72.0
            unit = "L"
            item = "shower"
            confidence = 0.85


            
    spacy_entities = []
    if doc:
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
        intent_val = "unknown"
        
    intent_display = "Unknown" if not intent_val or intent_val.lower() == "unknown" else intent_val.title()

    # Extract spaCy features
    distance_val = None
    duration_val = None
    source_val = None
    destination_val = None
    
    try:
        from app.nlp.spacy_service import extract_source_destination, extract_duration
        route_info = extract_source_destination(doc if doc is not None else text)
        source_val = route_info.get("source")
        destination_val = route_info.get("destination")
        
        duration_val = extract_duration(doc if doc is not None else text)
        if duration_val is None:
            if unit == "hours":
                duration_val = quantity
            elif unit in ["mins", "minutes"]:
                duration_val = quantity / 60.0
                
        if _wattage_result and _wattage_result.get("calculation_type") == "city_route":
            distance_val = float(_wattage_result.get("distance_km", 0.0))
        elif unit in ["km", "miles"]:
            distance_val = quantity
    except Exception:
        pass

    from app.nlp.entity_engine import extract_date_context
    date_ctx = extract_date_context(text)

    # Standardize 'activity' field
    activity_val = "veg_meal" if (category == "food" and item == "vegetarian_meal") else (item.lower().replace(" ", "_") if item else None)

    return {
        "category": category,
        "item": item,
        "activity": activity_val,
        "quantity": quantity,
        "unit": unit,
        "confidence": round(confidence, 2),
        "ambiguity": round(ambiguity, 2),
        "suggestions": suggestions,
        "original_text": text,
        "spacy_entities": spacy_entities,
        "intent": intent_display,
        "Intent": intent_display,
        # Pre-calculated values from intent-router (None when not applicable)
        "food_co2_kg":          _food_co2_kg,
        "shopping_co2_kg":      _shopping_co2,
        "pre_computed_emission": _wattage_result,  # wattage or city-route result
        "distance":             distance_val,
        "duration":             duration_val,
        "source":               source_val,
        "destination":          destination_val,
        "source_city":          source_val,
        "destination_city":     destination_val,
        "date_context":         date_ctx,
    }

def parse_compound_activity(text: str) -> List[Dict[str, Any]]:
    """
    Stage-2 Multi-Activity NLP — splits compound natural language input into
    individual activity dictionaries and parses each independently.

    Splitting conjunctions handled:
        and also | as well as | along with | then | plus | and | , (comma)

    Each segment is parsed independently through the full spaCy pipeline
    (parse_spacy → parse_activity_text) so Stage-1 behaviour is fully
    preserved for single-activity inputs.

    Food rescue pass:
        The spaCy PhraseMatcher fast-path sometimes returns category='lifestyle'
        for food items (e.g. idli, veg rice) when the label→category mapping
        is incomplete.  After parsing we check whether the item name resolves
        in the food emission KB and re-classify such segments as 'food'.
    """
    # Regex splitting on conjunctions — ordered longest-first to avoid
    # partial matches (e.g. "and also" must be tried before bare "and").
    # Uses lookarounds to avoid splitting thousands separator commas like 1,000.
    parts = re.split(
        r'\s+and\s+also\s+|\s+as\s+well\s+as\s+|\s+along\s+with\s+|\s+then\s+|\s+plus\s+|\s+and\s+|(?<!\d),\s*|,\s*(?!\d)',
        text,
        flags=re.IGNORECASE
    )

    results = []

    for part in parts:
        part_clean = part.strip()
        if not part_clean:
            continue

        # Strip leading conjunction/transition prefixes
        leading_pattern = r'^(?:and\s+also|as\s+well\s+as|along\s+with|and|then|plus|also|with)\s+'
        part_clean = re.sub(leading_pattern, '', part_clean, flags=re.IGNORECASE).strip()
        if not part_clean:
            continue

        # Parse this segment independently through the full pipeline
        parsed = parse_activity_text(part_clean)

        # Stamp the original segment text (not the full compound sentence)
        parsed["original_text"] = part_clean

        # ── Food rescue pass ─────────────────────────────────────────────────
        if parsed.get("category") == "lifestyle":
            try:
                from app.nlp.food_emission_factors import lookup_food
                item_name = parsed.get("item") or ""
                # Try matching the item label as a keyword against the food KB
                food_hit = lookup_food(item_name) or lookup_food(part_clean)
                if food_hit:
                    parsed["category"] = "food"
                    parsed["item"] = food_hit["name"]
                    if parsed.get("unit") in (None, "item", "unit", "serving"):
                        parsed["unit"] = food_hit["unit"]
                    # Attach pre-computed CO2 so calculate_emissions uses it directly
                    if parsed.get("food_co2_kg") is None:
                        parsed["food_co2_kg"] = food_hit["co2_kg"]
                    # Preserve confidence from spaCy match if it was high
                    if parsed.get("confidence", 0) < 0.80:
                        parsed["confidence"] = 0.90
                        parsed["ambiguity"] = 0.10
            except Exception:
                pass  # food rescue is best-effort; never crash

        # Update parsed 'activity' key after food rescue pass
        item_val = parsed.get("item")
        if parsed.get("category") == "food" and item_val == "vegetarian_meal":
            parsed["activity"] = "veg_meal"
        else:
            if item_val:
                parsed["activity"] = item_val.lower().replace(" ", "_")
            else:
                parsed["activity"] = None

        # Keep this segment if:
        #  - there is only one part (always keep), OR
        #  - it resolved to a real category (not lifestyle), OR
        #  - confidence is reasonable (> 0.30)
        keep = (
            len(parts) == 1
            or parsed["category"] != "lifestyle"
            or parsed["confidence"] > 0.30
        )
        if keep:
            results.append(parsed)

    if not results:
        # Emergency single fallback — parse the full text as one activity
        results.append(parse_activity_text(text))

    return results

