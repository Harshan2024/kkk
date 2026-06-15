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
