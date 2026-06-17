import pytest
from app.nlp.entity_engine import extract_entities, extract_multi_entities
from app.nlp.parser import parse_activity_text, parse_compound_activity

def test_advanced_transport():
    # Feature 2 & 8: Source & Destination + Route Extraction
    text = "I travelled from Chennai to Madurai by electric train"
    res = extract_entities(text)
    assert res.get("source") == "Chennai"
    assert res.get("destination") == "Madurai"
    assert res.get("source_city") == "Chennai"
    assert res.get("destination_city") == "Madurai"
    assert res.get("vehicle") == "electric_train"

def test_advanced_food():
    # Feature 3: Multiple Food Detection
    text = "I ate 3 idlis and 1 dosa"
    res = extract_multi_entities(text)
    assert len(res) == 2
    assert res[0].get("food") == "idli"
    assert res[0].get("quantity") == 3
    assert res[1].get("food") == "dosa"
    assert res[1].get("quantity") == 1

def test_advanced_energy():
    # Feature 1: Multi-Activity Extraction (Energy)
    text = "I used AC for 2 hours and TV for 3 hours"
    res = extract_multi_entities(text)
    assert len(res) == 2
    assert res[0].get("category") == "energy"
    assert res[0].get("device") == "air_conditioner"
    assert res[0].get("duration") == 2
    assert res[1].get("category") == "energy"
    assert res[1].get("device") == "television"
    assert res[1].get("duration") == 3

def test_advanced_shopping():
    # Feature 4: Shopping Extraction
    text = "I bought a laptop and mobile phone"
    res = extract_multi_entities(text)
    assert len(res) == 2
    assert res[0].get("product") == "laptop"
    assert res[1].get("product") == "smartphone"

def test_advanced_waste():
    # Feature 5: Waste Extraction
    text = "I disposed 2 kg plastic waste and 1 kg paper waste"
    res = extract_multi_entities(text)
    assert len(res) == 2
    assert res[0].get("waste") == "plastic_waste"
    assert res[0].get("weight") == 2
    assert res[1].get("waste") == "paper_waste"
    assert res[1].get("weight") == 1

def test_advanced_exercise():
    # Feature 10: Exercise Multi-Extraction & Safety
    text = "I ran 5 km and cycled 10 km"
    res = extract_multi_entities(text)
    assert len(res) == 2
    assert res[0].get("activity") == "running"
    assert res[0].get("distance") == 5
    assert res[1].get("activity") == "cycling"
    assert res[1].get("distance") == 10

def test_time_context_recognition():
    # Feature 6: Time Context
    text = "I travelled 10 km by metro yesterday"
    res = parse_activity_text(text)
    assert res.get("date_context") == "yesterday"

def test_unit_normalization():
    # Feature 7: Unit Normalization
    # 1. 120 minutes -> 2 hours
    res1 = parse_activity_text("Used AC for 120 minutes")
    assert res1.get("quantity") == 2
    assert res1.get("unit") == "hours"
    
    # 2. 1000 grams -> 1 kg
    res2 = parse_activity_text("I ate 1000 grams of chicken")
    assert res2.get("quantity") == 1
    assert res2.get("unit") == "kg"
    
    # 3. 10 kilometres -> 10 km
    res3 = parse_activity_text("I travelled 10 kilometres by car")
    assert res3.get("quantity") == 10
    assert res3.get("unit") == "km"

def test_unknown_entity_safety():
    # Feature 10: Practiced yoga -> activity = yoga
    res = extract_entities("I practiced yoga for 1 hour")
    assert res.get("activity") == "yoga"
    # Ensure it's not mapped to curd or other fabricated elements
    assert "food" not in res
    assert "curd" not in str(res).lower()

def test_multi_activity_detection():
    # 1. Transport + Food
    text_tf = "I travelled 10 km by metro and ate dosa"
    res_tf = parse_compound_activity(text_tf)
    assert len(res_tf) == 2
    assert res_tf[0].get("category") == "transport"
    assert res_tf[0].get("activity") == "metro"
    assert res_tf[0].get("quantity") == 10.0
    assert res_tf[0].get("unit") == "km"
    assert res_tf[0].get("confidence") >= 0.80
    assert res_tf[1].get("category") == "food"
    assert res_tf[1].get("activity") == "dosa"
    assert res_tf[1].get("quantity") == 1.0
    assert res_tf[1].get("confidence") >= 0.80

    # 2. Transport + Energy
    text_te = "I drove 20 km and used AC for 2 hours"
    res_te = parse_compound_activity(text_te)
    assert len(res_te) == 2
    assert res_te[0].get("category") == "transport"
    assert res_te[0].get("activity") == "petrol_car"
    assert res_te[0].get("quantity") == 20.0
    assert res_te[0].get("confidence") >= 0.70
    assert res_te[1].get("category") in ("appliances", "electricity")
    assert res_te[1].get("activity") in ("air_conditioner", "ac")
    assert res_te[1].get("quantity") == 2.0
    assert res_te[1].get("confidence") >= 0.80

    # 3. Food + Energy
    text_fe = "I ate idli and used fan for 3 hours"
    res_fe = parse_compound_activity(text_fe)
    assert len(res_fe) == 2
    assert res_fe[0].get("category") == "food"
    assert res_fe[0].get("activity") in ("idly", "idli")
    assert res_fe[0].get("quantity") == 1.0
    assert res_fe[1].get("category") == "appliances"
    assert res_fe[1].get("activity") == "fan"
    assert res_fe[1].get("quantity") == 3.0

    # 4. Three-Activity Input
    text_three = "I ate idli, travelled 5 km by bike and used fan for 3 hours"
    res_three = parse_compound_activity(text_three)
    assert len(res_three) == 3
    assert res_three[0].get("category") == "food"
    assert res_three[0].get("activity") in ("idly", "idli")
    assert res_three[1].get("category") == "transport"
    assert res_three[1].get("activity") in ("bicycle", "bike")
    assert res_three[1].get("quantity") == 5.0
    assert res_three[2].get("category") == "appliances"
    assert res_three[2].get("activity") == "fan"
    assert res_three[2].get("quantity") == 3.0

    # 5. Verify the required "veg meal" example maps to "veg_meal" and "Veg Meals" in food factors
    text_veg_meal = "I travelled 25 km by electric train and ate a veg meal"
    res_veg = parse_compound_activity(text_veg_meal)
    assert len(res_veg) == 2
    assert res_veg[0].get("category") == "transport"
    assert res_veg[0].get("activity") == "electric_train"
    assert res_veg[0].get("quantity") == 25.0
    assert res_veg[1].get("category") == "food"
    assert res_veg[1].get("activity") == "veg_meal"
    assert res_veg[1].get("quantity") == 1.0

