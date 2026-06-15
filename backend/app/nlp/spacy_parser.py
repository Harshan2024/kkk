from typing import Dict, Any, Optional
from app.nlp.spacy_service import (
    get_spacy_nlp,
    extract_numbers,
    extract_units,
    extract_locations,
    extract_source_destination,
    extract_duration
)
from app.nlp.entity_matcher import get_entity_matcher

LABEL_TO_CATEGORY = {
    "electric_train": "transport",
    "electric_bus": "transport",
    "electric_scooter": "transport",
    "electric_bike": "transport",
    "petrol_car": "transport",
    "diesel_car": "transport",
    "hybrid_car": "transport",
    "cng_car": "transport",
    "auto_rickshaw": "transport",
    "domestic_flight": "transport",
    "international_flight": "transport",
    "air_conditioner": "appliances",
    "washing_machine": "appliances",
    "vegetarian_meal": "food",
    "bicycle": "transport",
    "taxi": "transport",
    "electric_car": "transport"
}

DEFAULT_UNITS = {
    "transport": "km",
    "appliances": "hours",
    "food": "serving",
    "lifestyle": "item"
}

def parse_spacy(text: str) -> Optional[Dict[str, Any]]:
    """
    Tries to parse the text using spaCy and PhraseMatcher.
    Returns a parsed dictionary if a custom multi-word or normalized entity is matched.
    Otherwise returns None (triggers legacy fallback).
    """
    from app.nlp.entity_engine import normalize_units_in_text, extract_date_context
    normalized_text = normalize_units_in_text(text)
    
    nlp = get_spacy_nlp()
    if not nlp:
        return None
        
    doc = nlp(normalized_text)
    matcher = get_entity_matcher()
    matches = matcher.match(doc)
    
    if not matches:
        return None
        
    # Get the best match (PhraseMatcher sorts by span length descending)
    best_match = matches[0]
    item = best_match["label"]
    category = LABEL_TO_CATEGORY.get(item, "lifestyle")
    
    # Extract quantity and unit
    numbers = extract_numbers(doc)
    units = extract_units(doc)
    
    quantity = 1.0
    unit = DEFAULT_UNITS.get(category, "item")
    
    if numbers:
        quantity = float(numbers[0])
    if units:
        unit = units[0]
        
    # Standardize unit names
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
        
    # Location, source, destination, duration
    route_info = extract_source_destination(doc)
    source = route_info.get("source")
    destination = route_info.get("destination")
    
    duration = extract_duration(doc)
    if duration is None:
        if unit == "hours":
            duration = quantity
        elif unit in ["mins", "minutes"]:
            duration = quantity / 60.0
            
    distance = None
    if unit in ["km", "miles"]:
        distance = quantity
        
    # Feature 9: Confidence Levels
    # Exact Phrase Match = 1.00, PhraseMatcher Match = 0.98
    matched_phrase = best_match["text"]
    if matched_phrase in text:
        confidence = 1.00
    else:
        confidence = 0.98
    ambiguity = round(1.0 - confidence, 2)
    
    spacy_entities = []
    for ent in doc.ents:
        spacy_entities.append({
            "text": ent.text,
            "label": ent.label_
        })
        
    intent_display = category.title()
    
    # Mapping custom entities to database factors
    _food_co2_kg = None
    _shopping_co2 = None
    _wattage_result = None
    
    # Feature 6: Date Context
    date_ctx = extract_date_context(normalized_text)
    
    # Return the exact dictionary format that parse_activity_text returns
    return {
        "category": category,
        "item": item,
        "quantity": quantity,
        "unit": unit,
        "confidence": confidence,
        "ambiguity": ambiguity,
        "suggestions": [],
        "original_text": text,
        "spacy_entities": spacy_entities,
        "intent": intent_display,
        "Intent": intent_display,
        "food_co2_kg": _food_co2_kg,
        "shopping_co2_kg": _shopping_co2,
        "pre_computed_emission": _wattage_result,
        "distance": distance,
        "duration": duration,
        "source": source,
        "destination": destination,
        "source_city": source,
        "destination_city": destination,
        "date_context": date_ctx,
    }
