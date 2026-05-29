import pytest
from app.nlp.parser import parse_activity_text
from app.calculations.engines import (
    calculate_food_emission,
    calculate_transport_emission,
    calculate_appliance_emission
)

# Mock classes for database test isolation
class MockEmissionFactorRecord:
    def __init__(self, category, item_key, factor, unit, source="test"):
        self.category = category
        self.item_key = item_key
        self.factor = factor
        self.unit = unit
        self.source = source

class MockDbSession:
    def __init__(self):
        self.records = [
            # Food base ingredients
            MockEmissionFactorRecord("food", "beef", 60.0, "kg"),
            MockEmissionFactorRecord("food", "chicken", 6.9, "kg"),
            MockEmissionFactorRecord("food", "rice", 2.7, "kg"),
            MockEmissionFactorRecord("food", "curd", 2.2, "kg"),
            MockEmissionFactorRecord("food", "milk", 3.0, "kg"),
            MockEmissionFactorRecord("food", "vegetables", 0.5, "kg"),
            
            # Transport factors
            MockEmissionFactorRecord("transport", "petrol car", 0.192, "km"),
            MockEmissionFactorRecord("transport", "metro", 0.029, "km"),
            MockEmissionFactorRecord("transport", "flight", 0.255, "km"),
            MockEmissionFactorRecord("transport", "walking", 0.0, "km"),
            
            # Appliances / Electricity
            MockEmissionFactorRecord("electricity", "grid electricity", 0.70, "kWh"),
            MockEmissionFactorRecord("appliances", "ac", 1500.0, "W"),
            MockEmissionFactorRecord("appliances", "laptop", 60.0, "W"),
            MockEmissionFactorRecord("appliances", "washing machine", 500.0, "W"),
        ]

    def query(self, model_class):
        return MockQuery(self, model_class)

class MockQuery:
    def __init__(self, db_session, model_class):
        self.db = db_session
        self.model_class = model_class
        self.filters = {}

    def filter(self, *args):
        # Extract filter key-value pairs from SQLAlchemy BinaryExpressions
        for arg in args:
            try:
                # SQLAlchemy comparison structure: col == val
                col_name = arg.left.name
                val = arg.right.value
                self.filters[col_name] = val
            except AttributeError:
                # String fallback for complex or customized queries
                arg_str = str(arg)
                for r in self.db.records:
                    if f"'{r.item_key}'" in arg_str or f'"{r.item_key}"' in arg_str:
                        self.filters["item_key"] = r.item_key
                        break
        return self

    def first(self):
        # Scan mock database to find a matching record
        for r in self.db.records:
            match = True
            for col, val in self.filters.items():
                r_val = getattr(r, col, None)
                # Lowercase comparison if comparing strings
                if isinstance(r_val, str) and isinstance(val, str):
                    if r_val.lower() != val.lower():
                        match = False
                        break
                elif r_val != val:
                    match = False
                    break
            if match:
                return r
                
        # If no strict match (e.g. substring lookups for transport fallbacks)
        if "item_key" in self.filters:
            item_key_filter = self.filters["item_key"].lower()
            for r in self.db.records:
                if r.item_key in item_key_filter or item_key_filter in r.item_key:
                    return r
        return None

    def all(self):
        # Filter all records that match category
        if "category" in self.filters:
            return [r for r in self.db.records if r.category == self.filters["category"]]
        return self.db.records

# --- TESTS ---

def test_nlp_parser_basic():
    """
    Tests NLP entity parsing for various statements.
    """
    res1 = parse_activity_text("1 plate curd rice")
    assert res1["category"] == "food"
    assert res1["item"] == "curd rice"
    assert res1["quantity"] == 1.0
    assert res1["unit"] == "plate"

    res2 = parse_activity_text("Travelled 20 km by car")
    assert res2["category"] == "transport"
    assert res2["item"] == "petrol car"
    assert res2["quantity"] == 20.0
    assert res2["unit"] == "km"

    res3 = parse_activity_text("Used AC for 5 hours")
    assert res3["category"] == "appliances"
    assert res3["item"] == "ac"
    assert res3["quantity"] == 5.0
    assert res3["unit"] == "hours"

    # NLP maps 'twice' for washing machine directly to 'hours' (1h per run)
    res4 = parse_activity_text("Used washing machine twice")
    assert res4["category"] == "appliances"
    assert res4["item"] == "washing machine"
    assert res4["quantity"] == 2.0
    assert res4["unit"] == "hours"

def test_food_calculations(monkeypatch):
    """
    Tests food calculation engine.
    """
    db = MockDbSession()
    monkeypatch.setattr(db, "query", lambda model: MockQuery(db, model))

    # Test recipe curd rice: 200g rice (2.7 CO2e/kg) + 150g curd (2.2 CO2e/kg)
    # Emissions = (0.2 * 2.7) + (0.15 * 2.2) = 0.54 + 0.33 = 0.87 kgCO2e
    emissions, meta = calculate_food_emission(db, "curd rice", 1.0, "plate")
    assert abs(emissions - 0.87) < 0.01
    assert meta["calculation_type"] == "recipe_based"

    # Test weight based item: chicken 500g
    # Chicken: 6.9 kgCO2e/kg. Weight = 0.5kg.
    # Emissions = 0.5 * 6.9 = 3.45 kgCO2e
    emissions, meta = calculate_food_emission(db, "chicken", 500, "g")
    assert abs(emissions - 3.45) < 0.01
    assert meta["estimated_weight_kg"] == 0.5

def test_transport_calculations(monkeypatch):
    """
    Tests transport calculation engine.
    """
    db = MockDbSession()
    monkeypatch.setattr(db, "query", lambda model: MockQuery(db, model))

    # Test 10 km by petrol car (factor: 0.192)
    # Emissions = 10 * 0.192 = 1.92 kgCO2e
    emissions, meta = calculate_transport_emission(db, "petrol car", 10.0, "km")
    assert abs(emissions - 1.92) < 0.01

    # Test 10 miles by petrol car -> 16.0934 km
    # Emissions = 16.0934 * 0.192 = 3.09 kgCO2e
    emissions, meta = calculate_transport_emission(db, "petrol car", 10.0, "miles")
    assert abs(meta["distance_km"] - 16.09) < 0.02

def test_appliance_calculations(monkeypatch):
    """
    Tests appliance calculation engine.
    """
    db = MockDbSession()
    monkeypatch.setattr(db, "query", lambda model: MockQuery(db, model))

    # Test AC (1500W) for 5 hours. Grid factor (0.70)
    # Power = (1500 * 5) / 1000 = 7.5 kWh
    # Emissions = 7.5 * 0.70 = 5.25 kgCO2e
    emissions, meta = calculate_appliance_emission(db, "ac", 5.0)
    assert abs(emissions - 5.25) < 0.01
    assert meta["total_kwh"] == 7.5
