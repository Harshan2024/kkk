import pytest
import time
import spacy
from app.nlp.parser import parse_activity_text
from app.nlp.spacy_service import (
    get_spacy_nlp,
    extract_numbers,
    extract_units,
    extract_locations,
    extract_source_destination,
    extract_duration
)

def test_spacy_nlp_helpers():
    # 1. extract_numbers
    # The specification says: extract_numbers(text) returns [25, 3, 2] from "I travelled 25 km and used AC for 3 hours"
    nums = extract_numbers("I travelled 25 km and used AC for 3 hours")
    assert 25 in nums
    assert 3 in nums
    assert 2 in nums
    
    # 2. extract_units
    units = extract_units("I travelled 25 km and used AC for 3 hours")
    assert "km" in units
    assert "hours" in units

    # 3. extract_locations
    locs = extract_locations("I travelled from Chennai to Madurai")
    assert "Chennai" in locs
    assert "Madurai" in locs

    # 4. extract_source_destination
    route = extract_source_destination("I travelled from Chennai to Madurai")
    assert route["source"] == "Chennai"
    assert route["destination"] == "Madurai"

    # 5. extract_duration
    assert extract_duration("I used AC for 3 hours") == 3.0
    assert extract_duration("I used AC for 90 mins") == 1.5

def test_parser_integration():
    # Test "I travelled 25 km by electric train" -> distance = 25, unit = km
    res1 = parse_activity_text("I travelled 25 km by electric train")
    assert res1["distance"] == 25.0
    assert res1["unit"] == "km"
    assert res1["item"] == "electric_train"

    # Test "I travelled 15 km by electric scooter"
    res1_scooter = parse_activity_text("I travelled 15 km by electric scooter")
    assert res1_scooter["distance"] == 15.0
    assert res1_scooter["unit"] == "km"
    assert res1_scooter["item"] == "electric_scooter"

    # Test "I travelled 20 km by electric bus"
    res1_bus = parse_activity_text("I travelled 20 km by electric bus")
    assert res1_bus["distance"] == 20.0
    assert res1_bus["unit"] == "km"
    assert res1_bus["item"] == "electric_bus"

    # Test "I used AC for 3 hours" -> duration = 3, unit = hours
    res2 = parse_activity_text("I used AC for 3 hours")
    assert res2["duration"] == 3.0
    assert res2["unit"] == "hours"
    assert res2["item"] == "air_conditioner"

    # Test "I used AC for 2 hours"
    res2_ac2 = parse_activity_text("I used AC for 2 hours")
    assert res2_ac2["duration"] == 2.0
    assert res2_ac2["unit"] == "hours"
    assert res2_ac2["item"] == "air_conditioner"

    # Test "I ate a vegetarian meal"
    res_veg = parse_activity_text("I ate a vegetarian meal")
    assert res_veg["category"] == "food"
    assert res_veg["item"] == "vegetarian_meal"

    # Test "I travelled from Chennai to Madurai" -> source = Chennai, destination = Madurai
    res3 = parse_activity_text("I travelled from Chennai to Madurai")
    assert res3["source"] == "Chennai"
    assert res3["destination"] == "Madurai"

def test_spacy_singleton(monkeypatch):
    # Retrieve the nlp model instance multiple times and check identity
    nlp1 = get_spacy_nlp()
    nlp2 = get_spacy_nlp()
    assert nlp1 is nlp2

    # Verify that spacy.load is called at most once during runtime by checking the global state
    # Since it was already loaded, get_spacy_nlp should return immediately without calling load.
    load_called = 0
    original_load = spacy.load
    def mock_load(*args, **kwargs):
        nonlocal load_called
        load_called += 1
        return original_load(*args, **kwargs)
    
    monkeypatch.setattr(spacy, "load", mock_load)
    nlp3 = get_spacy_nlp()
    assert nlp3 is nlp1
    # Should not call spacy.load because it was already cached
    assert load_called == 0

def test_nlp_extraction_latency():
    # Target extraction latency: < 50ms per run
    # Perform a warm up run
    parse_activity_text("I travelled 25 km by electric train from Chennai to Madurai in 3 hours")
    
    start_time = time.perf_counter()
    for _ in range(50):
        parse_activity_text("I travelled 25 km by electric train from Chennai to Madurai in 3 hours")
    end_time = time.perf_counter()
    avg_latency_ms = ((end_time - start_time) / 50) * 1000.0
    print(f"Average extraction latency: {avg_latency_ms:.2f}ms")
    assert avg_latency_ms < 50.0

def test_disabled_endpoints():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)

    assert client.get("/api/v1/analytics/forecast").status_code == 503
    assert client.get("/api/v1/forecast").status_code == 503
    assert client.get("/observability/metrics").status_code == 200
    assert client.get("/api/v1/habit-analysis").status_code == 200


def test_transport_factor_integration(monkeypatch):
    from app.calculations.engines import calculate_transport_emission
    from tests.test_backend import MockDbSession, MockQuery
    
    db = MockDbSession()
    monkeypatch.setattr(db, "query", lambda model: MockQuery(db, model))
    
    # 1. "I travelled 25 km by electric train" -> entity = electric_train, factor = 0.020, carbon = 0.50
    res1 = parse_activity_text("I travelled 25 km by electric train")
    assert res1["item"] == "electric_train"
    emissions1, meta1 = calculate_transport_emission(db, res1["item"], res1["distance"], res1["unit"])
    assert meta1["vehicle_mapped"] == "electric_train"
    assert abs(meta1["emission_factor"] - 0.020) < 0.001
    assert abs(emissions1 - 0.50) < 0.01
    
    # 2. "I travelled 20 km by electric bus" -> factor = 0.060
    res2 = parse_activity_text("I travelled 20 km by electric bus")
    assert res2["item"] == "electric_bus"
    emissions2, meta2 = calculate_transport_emission(db, res2["item"], res2["distance"], res2["unit"])
    assert meta2["vehicle_mapped"] == "electric_bus"
    assert abs(meta2["emission_factor"] - 0.060) < 0.001
    assert abs(emissions2 - 1.20) < 0.01
    
    # 3. "I travelled 15 km by electric scooter" -> factor = 0.015
    res3 = parse_activity_text("I travelled 15 km by electric scooter")
    assert res3["item"] == "electric_scooter"
    emissions3, meta3 = calculate_transport_emission(db, res3["item"], res3["distance"], res3["unit"])
    assert meta3["vehicle_mapped"] == "electric_scooter"
    assert abs(meta3["emission_factor"] - 0.015) < 0.001
    assert abs(emissions3 - 0.225) < 0.01
