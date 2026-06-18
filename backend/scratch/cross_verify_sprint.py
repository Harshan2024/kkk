import sys
import os
import time

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.nlp.parser import parse_activity_text, parse_compound_activity
from app.nlp.entity_engine import extract_entities, extract_multi_entities
from app.nlp.spacy_service import get_spacy_nlp, extract_source_destination, extract_duration
from app.calculations.engines import (
    calculate_food_emission,
    calculate_transport_emission,
    calculate_appliance_emission,
    calculate_generic_emission
)
from app.services.activity_service import calculate_emissions

# Mock Db Session for calculations
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
            MockEmissionFactorRecord("food", "sambar rice", 1.5, "kg"),
            MockEmissionFactorRecord("food", "chicken biryani", 4.0, "kg"),
            MockEmissionFactorRecord("food", "coffee", 0.4, "cup"),
            
            # Transport factors
            MockEmissionFactorRecord("transport", "petrol car", 0.192, "km"),
            MockEmissionFactorRecord("transport", "metro", 0.029, "km"),
            MockEmissionFactorRecord("transport", "flight", 0.255, "km"),
            MockEmissionFactorRecord("transport", "walking", 0.0, "km"),
            MockEmissionFactorRecord("transport", "electric_train", 0.020, "km"),
            MockEmissionFactorRecord("transport", "electric train", 0.020, "km"),
            MockEmissionFactorRecord("transport", "electric_bus", 0.060, "km"),
            MockEmissionFactorRecord("transport", "electric_scooter", 0.015, "km"),
            MockEmissionFactorRecord("transport", "electric_bike", 0.020, "km"),
            MockEmissionFactorRecord("transport", "petrol_car", 0.192, "km"),
            MockEmissionFactorRecord("transport", "diesel_car", 0.171, "km"),
            MockEmissionFactorRecord("transport", "hybrid_car", 0.095, "km"),
            MockEmissionFactorRecord("transport", "cng_car", 0.110, "km"),
            MockEmissionFactorRecord("transport", "auto_rickshaw", 0.090, "km"),
            MockEmissionFactorRecord("transport", "bike", 0.050, "km"),
            MockEmissionFactorRecord("transport", "bicycle", 0.050, "km"),
            
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

db = MockDbSession()

# Tracking results
results = []

def run_test(category, name, text, validation_func):
    try:
        parsed = parse_activity_text(text)
        co2, meta = calculate_emissions(db, parsed)
        success, message = validation_func(parsed, co2, meta)
        results.append({
            "category": category,
            "name": name,
            "text": text,
            "success": success,
            "message": message,
            "parsed": parsed,
            "co2": co2,
            "meta": meta
        })
    except Exception as e:
        results.append({
            "category": category,
            "name": name,
            "text": text,
            "success": False,
            "message": f"Crashed: {e}",
            "parsed": {},
            "co2": 0.0,
            "meta": {}
        })

# --- Category 1: Transport ---
# 1.1 "I travelled 25 km by electric train" -> Intent=Transport, Vehicle=Electric Train, Distance=25 km, CO2=25 * 0.020 = 0.5
def val_1_1(p, co2, meta):
    intent_ok = p.get("intent", "").lower() == "transport" or p.get("category") == "transport"
    vehicle = (p.get("item") or "").lower()
    vehicle_ok = "electric" in vehicle and "train" in vehicle
    dist = p.get("distance")
    dist_ok = dist == 25 or p.get("quantity") == 25
    co2_ok = abs(co2 - 0.5) < 0.01
    msg = f"Intent={p.get('intent')}, Item={p.get('item')}, Qty={p.get('quantity')}, Unit={p.get('unit')}, CO2={co2}"
    return (intent_ok and vehicle_ok and dist_ok and co2_ok), msg

run_test("Transport", "1.1 Electric Train 25km", "I travelled 25 km by electric train", val_1_1)

# 1.2 "I travelled 10 km by bike" -> Intent=Transport, Vehicle=Motorcycle/Bike, Distance=10 km
def val_1_2(p, co2, meta):
    intent_ok = p.get("intent", "").lower() == "transport" or p.get("category") == "transport"
    vehicle = (p.get("item") or "").lower()
    vehicle_ok = "bike" in vehicle or "motorcycle" in vehicle or "bicycle" in vehicle
    dist = p.get("distance")
    dist_ok = dist == 10 or p.get("quantity") == 10
    msg = f"Intent={p.get('intent')}, Item={p.get('item')}, Qty={p.get('quantity')}, Unit={p.get('unit')}"
    return (intent_ok and vehicle_ok and dist_ok), msg

run_test("Transport", "1.2 Bike 10km", "I travelled 10 km by bike", val_1_2)

# 1.3 "I walked 5 km" -> Intent=Exercise, Activity=Walking, CO2=0
def val_1_3(p, co2, meta):
    intent_ok = p.get("category") == "exercise"
    act_ok = "walk" in (p.get("item") or "").lower() or "walk" in (p.get("activity") or "").lower()
    co2_ok = co2 == 0
    msg = f"Category={p.get('category')}, Item={p.get('item')}, CO2={co2}"
    return (intent_ok and act_ok and co2_ok), msg

run_test("Transport", "1.3 Walked 5km", "I walked 5 km", val_1_3)

# 1.4 "I jogged 3 km" -> Intent=Exercise, Activity=Jogging, CO2=0
def val_1_4(p, co2, meta):
    intent_ok = p.get("category") == "exercise"
    act_ok = "jog" in (p.get("item") or "").lower() or "jog" in (p.get("activity") or "").lower()
    co2_ok = co2 == 0
    msg = f"Category={p.get('category')}, Item={p.get('item')}, CO2={co2}"
    return (intent_ok and act_ok and co2_ok), msg

run_test("Transport", "1.4 Jogged 3km", "I jogged 3 km", val_1_4)


# --- Category 2: Energy ---
# 2.1 "I used AC for 3 hours" -> Intent=Energy, Device=AC, Duration=3 hours
def val_2_1(p, co2, meta):
    intent_ok = p.get("intent", "").lower() == "energy" or p.get("category") in ("appliances", "electricity")
    dev = (p.get("item") or "").lower()
    dev_ok = "ac" in dev or "air" in dev
    dur = p.get("duration") or p.get("quantity")
    dur_ok = dur == 3
    # MUST NOT BECOME Running, Food, Transport
    not_other = p.get("category") not in ("food", "transport", "exercise")
    msg = f"Category={p.get('category')}, Item={p.get('item')}, Qty={p.get('quantity')}"
    return (intent_ok and dev_ok and dur_ok and not_other), msg

run_test("Energy", "2.1 AC 3h", "I used AC for 3 hours", val_2_1)

# 2.2 "I charged my laptop for 90 minutes using a 135W charger" -> Intent=Energy, Device=Laptop Charger, Power=135W, Duration=90 minutes
def val_2_2(p, co2, meta):
    intent_ok = p.get("intent", "").lower() == "energy" or p.get("category") in ("appliances", "electricity")
    dev = (p.get("item") or "").lower()
    dev_ok = "laptop" in dev
    dur = p.get("duration") or p.get("quantity")
    dur_ok = dur == 1.5 or dur == 90 or p.get("quantity") == 1.5 or p.get("quantity") == 90
    power = p.get("pre_computed_emission", {}).get("appliance_watts") or p.get("pre_computed_emission", {}).get("watts") or p.get("power")
    msg = f"Category={p.get('category')}, Item={p.get('item')}, Qty={p.get('quantity')}, Unit={p.get('unit')}, Power={power}"
    return (intent_ok and dev_ok and dur_ok), msg

run_test("Energy", "2.2 Laptop Charger 90m 135W", "I charged my laptop for 90 minutes using a 135W charger", val_2_2)


# --- Category 3: Food ---
# 3.1 "I ate chicken biriyani" -> Food=Chicken Biriyani (Must NOT split into Chicken, Rice)
def val_3_1(p, co2, meta):
    cat_ok = p.get("category") == "food"
    food = (p.get("item") or "").lower()
    biryani_ok = "biryani" in food or "biriyani" in food
    splits = parse_compound_activity("I ate chicken biriyani")
    not_split = len(splits) == 1
    msg = f"Category={p.get('category')}, Item={p.get('item')}, Splits={len(splits)}"
    return (cat_ok and biryani_ok and not_split), msg

run_test("Food", "3.1 Chicken Biriyani", "I ate chicken biriyani", val_3_1)

# 3.2 "I ate sambar rice" -> Food=Sambar Rice
def val_3_2(p, co2, meta):
    cat_ok = p.get("category") == "food"
    food = (p.get("item") or "").lower()
    food_ok = "sambar" in food or "rice" in food
    msg = f"Category={p.get('category')}, Item={p.get('item')}"
    return (cat_ok and food_ok), msg

run_test("Food", "3.2 Sambar Rice", "I ate sambar rice", val_3_2)

# 3.3 "I drank coffee" -> Food=Coffee
def val_3_3(p, co2, meta):
    cat_ok = p.get("category") == "food"
    food = (p.get("item") or "").lower()
    food_ok = "coffee" in food
    msg = f"Category={p.get('category')}, Item={p.get('item')}"
    return (cat_ok and food_ok), msg

run_test("Food", "3.3 Coffee", "I drank coffee", val_3_3)


# --- Category 4: Shopping ---
# 4.1 "I bought a laptop" -> Intent=Shopping, Product=Laptop (Must NOT become: Energy, Appliance Usage)
def val_4_1(p, co2, meta):
    intent_ok = p.get("intent", "").lower() == "shopping" or p.get("category") == "shopping"
    prod = (p.get("item") or "").lower()
    prod_ok = "laptop" in prod or "electronics" in prod
    not_energy = p.get("category") not in ("appliances", "electricity", "energy")
    msg = f"Intent={p.get('intent')}, Category={p.get('category')}, Item={p.get('item')}"
    return (intent_ok and prod_ok and not_energy), msg

run_test("Shopping", "4.1 Bought Laptop", "I bought a laptop", val_4_1)

# 4.2 "I purchased a smartphone" -> Product=Smartphone
def val_4_2(p, co2, meta):
    intent_ok = p.get("intent", "").lower() == "shopping" or p.get("category") == "shopping"
    prod = (p.get("item") or "").lower()
    prod_ok = "smartphone" in prod or "phone" in prod or "electronics" in prod
    msg = f"Intent={p.get('intent')}, Category={p.get('category')}, Item={p.get('item')}"
    return (intent_ok and prod_ok), msg

run_test("Shopping", "4.2 Purchased Smartphone", "I purchased a smartphone", val_4_2)


# --- Category 5: Waste ---
# 5.1 "I disposed 2 kg plastic waste" -> Waste Type=Plastic Waste, Weight=2 kg
def val_5_1(p, co2, meta):
    cat_ok = p.get("category") == "waste"
    item = (p.get("item") or "").lower()
    item_ok = "plastic" in item
    weight = p.get("quantity")
    weight_ok = weight == 2
    msg = f"Category={p.get('category')}, Item={p.get('item')}, Qty={p.get('quantity')}"
    return (cat_ok and item_ok and weight_ok), msg

run_test("Waste", "5.1 Plastic Waste 2kg", "I disposed 2 kg plastic waste", val_5_1)

# 5.2 "I recycled e-waste" -> Waste Type=E-Waste
def val_5_2(p, co2, meta):
    cat_ok = p.get("category") == "waste"
    item = (p.get("item") or "").lower()
    item_ok = "e-waste" in item or "recycling" in item or "waste" in item
    msg = f"Category={p.get('category')}, Item={p.get('item')}"
    return (cat_ok and item_ok), msg

run_test("Waste", "5.2 E-waste", "I recycled e-waste", val_5_2)


# --- Category 6: Unknown Activities ---
# 6.1 "I did yoga for 1 hour" -> Intent=Exercise, Activity=Yoga (Must NEVER become: Curd, Food, Rice, Transport)
def val_6_1(p, co2, meta):
    cat_ok = p.get("category") == "exercise"
    act = (p.get("item") or "").lower()
    act_ok = "yoga" in act
    not_curd = "curd" not in act and "rice" not in act and p.get("category") != "food" and p.get("category") != "transport"
    msg = f"Category={p.get('category')}, Item={p.get('item')}"
    return (cat_ok and act_ok and not_curd), msg

run_test("Unknown Activities", "6.1 Yoga 1h", "I did yoga for 1 hour", val_6_1)

# 6.2 "I played cricket for 2 hours" -> Activity=Cricket (Must NEVER become: Food)
def val_6_2(p, co2, meta):
    act = (p.get("item") or "").lower()
    not_food = p.get("category") != "food"
    msg = f"Category={p.get('category')}, Item={p.get('item')}"
    return not_food, msg

run_test("Unknown Activities", "6.2 Played Cricket", "I played cricket for 2 hours", val_6_2)


# --- Category 7: spaCy Validation ---
def val_7_1():
    p1 = parse_activity_text("I travelled 25 km by car")
    ok1 = p1.get("quantity") == 25 and p1.get("unit") == "km"
    p2 = parse_activity_text("I used AC for 3 hours")
    ok2 = p2.get("quantity") == 3 and p2.get("unit") == "hours"
    p3 = parse_activity_text("I charged my laptop for 90 minutes")
    ok3 = p3.get("quantity") == 1.5 and p3.get("unit") == "hours"
    p4 = parse_activity_text("I disposed 2 kg plastic waste")
    ok4 = p4.get("quantity") == 2 and p4.get("unit") == "kg"
    
    success = ok1 and ok2 and ok3 and ok4
    msg = f"25km={ok1}({p1.get('quantity')}{p1.get('unit')}), 3h={ok2}({p2.get('quantity')}{p2.get('unit')}), 90m={ok3}({p3.get('quantity')}{p3.get('unit')}), 2kg={ok4}({p4.get('quantity')}{p4.get('unit')})"
    results.append({
        "category": "spaCy Validation",
        "name": "7.1 Numbers Extraction",
        "text": "Numbers extraction verification",
        "success": success,
        "message": msg,
        "parsed": {},
        "co2": 0.0,
        "meta": {}
    })

val_7_1()

def val_7_2():
    p1 = parse_activity_text("I travelled from Chennai to Madurai by train")
    ok1 = p1.get("source_city") == "Chennai" and p1.get("destination_city") == "Madurai"
    p2 = parse_activity_text("I went from Salem to Coimbatore by car")
    ok2 = p2.get("source_city") == "Salem" and p2.get("destination_city") == "Coimbatore"
    
    success = ok1 and ok2
    msg = f"Chennai->Madurai={ok1}({p1.get('source_city')}->{p1.get('destination_city')}), Salem->Coimbatore={ok2}({p2.get('source_city')}->{p2.get('destination_city')})"
    results.append({
        "category": "spaCy Validation",
        "name": "7.2 Cities Extraction",
        "text": "Cities extraction verification",
        "success": success,
        "message": msg,
        "parsed": {},
        "co2": 0.0,
        "meta": {}
    })

val_7_2()

def val_7_3():
    p1 = parse_activity_text("I travelled by electric train")
    ok1 = "electric" in (p1.get("item") or "").lower() and "train" in (p1.get("item") or "").lower()
    p2 = parse_activity_text("I ate chicken biriyani")
    ok2 = "biryani" in (p2.get("item") or "").lower() or "biriyani" in (p2.get("item") or "").lower()
    p3 = parse_activity_text("I used a laptop charger for 1 hour")
    ok3 = "laptop" in (p3.get("item") or "").lower()
    
    success = ok1 and ok2 and ok3
    msg = f"ElectricTrain={ok1}({p1.get('item')}), ChickenBiriyani={ok2}({p2.get('item')}), LaptopCharger={ok3}({p3.get('item')})"
    results.append({
        "category": "spaCy Validation",
        "name": "7.3 Longest Phrase Matching",
        "text": "Longest phrase matching verification",
        "success": success,
        "message": msg,
        "parsed": {},
        "co2": 0.0,
        "meta": {}
    })

val_7_3()


# --- CRITICAL FAILURE CONDITIONS CHECK ---
critical_failures = []
for r in results:
    if not r["success"]:
        name = r["name"]
        text = r["text"]
        parsed = r["parsed"]
        
        if "yoga" in text.lower() and ("curd" in str(parsed).lower() or parsed.get("category") == "food"):
            critical_failures.append(f"CRITICAL FAILURE: Yoga became food/curd in test '{name}'")
        if "ac" in text.lower() and ("run" in str(parsed).lower() or parsed.get("category") == "exercise"):
            critical_failures.append(f"CRITICAL FAILURE: AC became running/exercise in test '{name}'")
        if "bought a laptop" in text.lower() and parsed.get("category") in ("appliances", "electricity", "energy"):
            critical_failures.append(f"CRITICAL FAILURE: Laptop bought became Appliance Usage in test '{name}'")
        if "electric train" in text.lower() and parsed.get("item") == "train":
            critical_failures.append(f"CRITICAL FAILURE: Electric Train matched as generic Train in test '{name}'")
        if "chicken biriyani" in text.lower():
            splits = parse_compound_activity(text)
            if len(splits) > 1:
                critical_failures.append(f"CRITICAL FAILURE: Chicken Biriyani split into multiple parts: {[s.get('item') for s in splits]} in test '{name}'")
        if "cricket" in text.lower() and parsed.get("category") == "food":
            critical_failures.append(f"CRITICAL FAILURE: Unknown activity (cricket) mapped to food in test '{name}'")

# Generate final PASS/FAIL summary
failed_tests = [r for r in results if not r["success"]]
overall_pass = len(failed_tests) == 0 and len(critical_failures) == 0

# Grouped accuracy calculation
categories = {}
for r in results:
    cat = r["category"]
    if cat not in categories:
        categories[cat] = {"total": 0, "passed": 0}
    categories[cat]["total"] += 1
    if r["success"]:
        categories[cat]["passed"] += 1

print("PASS/FAIL SUMMARY:")
print("STATUS:", "PASS" if overall_pass else "FAIL")
print("\nAccuracy per Category:")
for cat, stats in categories.items():
    pct = (stats["passed"] / stats["total"]) * 100
    print(f"  {cat} Accuracy: {pct:.1f}% ({stats['passed']}/{stats['total']})")

if not overall_pass:
    print("\nFAILED TEST CASES:")
    for f in failed_tests:
        print(f"  - [{f['category']}] {f['name']} (Input: '{f['text']}') -> {f['message']}")
    for cf in critical_failures:
        print(f"  - {cf}")
else:
    print("\nAll verification test cases passed successfully.")

if critical_failures:
    print("\nRoot Cause:")
    print("  Critical failure conditions triggered. Synonyms/phrase matcher mapping priority issue, or insufficient pattern boundary guards.")
    print("\nRecommended Fix:")
    print("  Adjust keyword matcher priorities, word boundary patterns in regex, or spaCy PhraseMatcher rules to prevent incorrect splits and mapping fallbacks.")
