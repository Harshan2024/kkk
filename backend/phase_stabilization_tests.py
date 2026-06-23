import unittest
from datetime import datetime
from typing import Dict, Any, Tuple
import json

from app.nlp.parser import parse_activity_text, parse_compound_activity
from app.nlp.entity_engine import extract_entities, extract_multi_entities
from app.calculations.engines import (
    calculate_food_emission,
    calculate_transport_emission,
    calculate_appliance_emission,
    calculate_generic_emission
)
from app.api.endpoints import sanitize_category, sanitize_float, canonical_display

# Reuse the DB Session Mock pattern from test_backend.py
class MockEmissionFactorRecord:
    def __init__(self, category, item_key, factor, unit, source="test", display_name=None, region="Global"):
        self.category = category
        self.item_key = item_key
        self.factor = factor
        self.unit = unit
        self.source = source
        self.display_name = display_name or item_key.title()
        self.region = region

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
            MockEmissionFactorRecord("food", "chicken biryani", 1.785, "plate"),
            MockEmissionFactorRecord("food", "chicken biriyani", 1.785, "plate"),
            
            # Transport factors
            MockEmissionFactorRecord("transport", "petrol car", 0.192, "km"),
            MockEmissionFactorRecord("transport", "train", 0.041, "km"),
            MockEmissionFactorRecord("transport", "flight", 0.255, "km"),
            MockEmissionFactorRecord("transport", "walking", 0.0, "km"),
            MockEmissionFactorRecord("transport", "electric_train", 0.020, "km"),
            MockEmissionFactorRecord("transport", "electric_bus", 0.060, "km"),
            MockEmissionFactorRecord("transport", "electric_scooter", 0.015, "km"),
            MockEmissionFactorRecord("transport", "electric_bike", 0.020, "km"),
            MockEmissionFactorRecord("transport", "petrol_car", 0.192, "km"),
            
            # Appliances / Electricity
            MockEmissionFactorRecord("appliances", "ac", 1500.0, "W"),
            MockEmissionFactorRecord("appliances", "laptop", 60.0, "W"),
            MockEmissionFactorRecord("appliances", "washing machine", 500.0, "W"),
            
            # Waste factors
            MockEmissionFactorRecord("waste", "e-waste", 0.5, "kg"),
            MockEmissionFactorRecord("waste", "plastic waste", 0.8, "kg")
        ]

    def query(self, model_class):
        return MockQuery(self, model_class)

class MockQuery:
    def __init__(self, db_session, model_class):
        self.db = db_session
        self.model_class = model_class
        self.filters = {}

    def filter(self, *args):
        for arg in args:
            try:
                col_name = arg.left.name
                val = arg.right.value
                self.filters[col_name] = val
            except AttributeError:
                arg_str = str(arg)
                for r in self.db.records:
                    if f"'{r.item_key}'" in arg_str or f'"{r.item_key}"' in arg_str:
                        self.filters["item_key"] = r.item_key
                        break
        return self

    def first(self):
        for r in self.db.records:
            match = True
            for col, val in self.filters.items():
                r_val = getattr(r, col, None)
                if isinstance(r_val, str) and isinstance(val, str):
                    if r_val.lower() != val.lower():
                        match = False
                        break
                elif r_val != val:
                    match = False
                    break
            if match:
                return r
                
        if "item_key" in self.filters:
            item_key_filter = self.filters["item_key"].lower()
            for r in self.db.records:
                if r.item_key in item_key_filter or item_key_filter in r.item_key:
                    return r
        return None

    def all(self):
        if "category" in self.filters:
            return [r for r in self.db.records if r.category == self.filters["category"]]
        return self.db.records


class TestCarbonTrackerStabilization(unittest.TestCase):
    def setUp(self):
        self.db = MockDbSession()

    # =========================================================================
    # SECTION 1: NLP STABILIZATION TESTS
    # =========================================================================
    def test_intent_detection(self):
        """Verify Intent classifications mapping for transport, energy, food, waste"""
        res_transport = parse_activity_text("I travelled 10 km by metro")
        self.assertEqual(res_transport["category"], "transport")

        res_energy = parse_activity_text("Used AC for 2 hours")
        self.assertEqual(res_energy["category"], "appliances")

        res_food = parse_activity_text("I ate chicken biriyani")
        self.assertEqual(res_food["category"], "food")

        res_waste = parse_activity_text("recycled 1 kg e-waste")
        self.assertEqual(res_waste["category"], "waste")

    def test_entity_and_quantity_extraction(self):
        """Verify quantity extraction, unit extraction and normalization"""
        # Unit conversion: 120 minutes -> 2 hours
        res1 = parse_activity_text("Used AC for 120 minutes")
        self.assertEqual(res1["quantity"], 2.0)
        self.assertEqual(res1["unit"], "hours")

        # Unit conversion: 1000 grams -> 1 kg
        res2 = parse_activity_text("ate 1000 grams of chicken")
        self.assertEqual(res2["quantity"], 1.0)
        self.assertEqual(res2["unit"], "kg")

        # Unit conversion: 10 kilometres -> 10 km
        res3 = parse_activity_text("travelled 10 kilometres by car")
        self.assertEqual(res3["quantity"], 10.0)
        self.assertEqual(res3["unit"], "km")

    def test_mixed_sentence_compound_nlp(self):
        """Verify the complex mixed sentence input handles all entities correctly"""
        complex_text = "I travelled 20 km by train, ate chicken biriyani, used AC for 3 hours and recycled 1 kg e-waste."
        splits = parse_compound_activity(complex_text)
        
        self.assertEqual(len(splits), 4)
        
        # Part 1: transport
        self.assertEqual(splits[0]["category"], "transport")
        self.assertEqual(splits[0]["item"], "train")
        self.assertEqual(splits[0]["quantity"], 20.0)
        self.assertEqual(splits[0]["unit"], "km")

        # Part 2: food
        self.assertEqual(splits[1]["category"], "food")
        self.assertTrue("biry" in splits[1]["item"].lower() or "biriy" in splits[1]["item"].lower())
        self.assertEqual(splits[1]["quantity"], 1.0)

        # Part 3: AC
        self.assertEqual(splits[2]["category"], "appliances")
        self.assertIn(splits[2]["item"].lower(), ["ac", "air_conditioner", "air conditioner"])
        self.assertEqual(splits[2]["quantity"], 3.0)
        self.assertEqual(splits[2]["unit"], "hours")

        # Part 4: waste
        self.assertEqual(splits[3]["category"], "waste")
        self.assertTrue("e-waste" in splits[3]["item"].lower() or "e_waste" in splits[3]["item"].lower())
        self.assertEqual(splits[3]["quantity"], 1.0)
        self.assertEqual(splits[3]["unit"], "kg")

    # =========================================================================
    # SECTION 2: CARBON ENGINE STABILIZATION TESTS
    # =========================================================================
    def test_carbon_engines_determinism(self):
        """Verify that the same inputs always return the exact same carbon value"""
        # Transport
        val1, meta1 = calculate_transport_emission(self.db, "petrol car", 10.0, "km")
        val2, meta2 = calculate_transport_emission(self.db, "petrol car", 10.0, "km")
        self.assertEqual(val1, val2)
        self.assertEqual(val1, 1.92) # 10 km * 0.192

        # Food (Chicken Biryani serves 1.0 plate)
        val3, meta3 = calculate_food_emission(self.db, "chicken biryani", 1.0, "plate")
        val4, meta4 = calculate_food_emission(self.db, "chicken biryani", 1.0, "plate")
        self.assertEqual(val3, val4)
        self.assertEqual(val3, 2.5) # from FOOD_FACTORS

        # Appliance
        val5, meta5 = calculate_appliance_emission(self.db, "ac", 2.0, region="Global")
        val6, meta6 = calculate_appliance_emission(self.db, "ac", 2.0, region="Global")
        self.assertEqual(val5, val6)
        self.assertEqual(val5, 2.46) # (1500W * 2h)/1000 * 0.82 grid factor

    # =========================================================================
    # SECTION 3: MULTI ENTITY STABILIZATION TESTS
    # =========================================================================
    def test_multi_entity_bounds(self):
        """Verify that 1, 2, 5, and 10 entities are processed independently and sum correctly"""
        test_inputs = [
            # 1 Entity
            ["I drove 10 km by car"],
            # 2 Entities
            ["I drove 10 km by car", "I used AC for 2 hours"],
            # 5 Entities
            ["I drove 10 km by car", "I used AC for 2 hours", "ate chicken biryani", "recycled 1 kg e-waste", "recycled 2 kg plastic"],
            # 10 Entities
            [
                "I drove 10 km by car", "I used AC for 2 hours", "ate chicken biryani", 
                "recycled 1 kg e-waste", "recycled 2 kg plastic", "used fan for 5 hours", 
                "ate vegetables", "used laptop for 3 hours", "travelled 10 km by metro",
                "used washer for 1 hour"
            ]
        ]

        for case in test_inputs:
            joined = " and ".join(case)
            splits = parse_compound_activity(joined)
            self.assertEqual(len(splits), len(case))
            
            total_calc = 0.0
            for idx, p in enumerate(splits):
                cat = p.get("category")
                item = p.get("item")
                qty = p.get("quantity")
                unit = p.get("unit")
                
                # Check that fields are visible
                self.assertIsNotNone(cat)
                self.assertIsNotNone(item)
                self.assertIsNotNone(qty)
                self.assertIsNotNone(unit)

                # Compute emissions using corresponding calculation engine
                if cat == "transport":
                    val, _ = calculate_transport_emission(self.db, item, qty, unit)
                elif cat == "appliances":
                    val, _ = calculate_appliance_emission(self.db, item, qty)
                elif cat == "food":
                    val, _ = calculate_food_emission(self.db, item, qty, unit, food_co2_kg=p.get("food_co2_kg"))
                else:
                    val, _ = calculate_generic_emission(self.db, cat, item, qty, unit)
                
                total_calc += val
            
            self.assertGreater(total_calc, 0.0)

    # =========================================================================
    # SECTION 5: API CONTRACTS TESTS
    # =========================================================================
    def test_api_success_envelope(self):
        """Verify mock API response wraps success/error envelopes strictly"""
        # Testing endpoints.py response formats helper
        from app.api.endpoints import make_standardized_parse_response
        
        success_res = make_standardized_parse_response(
            status="success",
            intent="transport",
            entities=[],
            total_carbon=1.5,
            success=True
        )
        self.assertTrue(success_res["success"])
        self.assertEqual(success_res["status"], "success")
        self.assertEqual(success_res["total_carbon"], 1.5)

        error_res = make_standardized_parse_response(
            status="error",
            error="entity_not_found",
            success=False
        )
        self.assertFalse(error_res["success"])
        self.assertEqual(error_res["status"], "error")
        self.assertEqual(error_res["error"], "entity_not_found")


if __name__ == "__main__":
    unittest.main()
