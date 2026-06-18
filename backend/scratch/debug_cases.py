import sys
import os

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.nlp.parser import parse_activity_text, parse_compound_activity
from app.nlp.entity_engine import extract_entities
from app.services.activity_service import calculate_emissions
from scratch.cross_verify_sprint import MockDbSession

db = MockDbSession()
failures = []

def assert_val(label, val, expected):
    if val != expected:
        msg = f"FAIL: {label} (got {repr(val)}, expected {repr(expected)})"
        failures.append(msg)
        print(msg)
    else:
        print(f"PASS: {label} (got {repr(val)})")

def assert_approx(label, val, expected, tolerance=0.01):
    if abs(val - expected) > tolerance:
        msg = f"FAIL: {label} (got {val:.4f}, expected {expected:.4f})"
        failures.append(msg)
        print(msg)
    else:
        print(f"PASS: {label} (got {val:.2f})")

# 1. LONGEST PHRASE MATCHING TESTS
print("\n--- LONGEST PHRASE MATCHING TESTS ---")
# Laptop Charger > Laptop
p = parse_activity_text("I used a Laptop Charger")
assert_val("Laptop Charger item name", p.get("item"), "laptop_charger")
assert_val("Laptop Charger category", p.get("category"), "appliances")

# Electric Train > Train
p = parse_activity_text("I travelled by Electric Train")
assert_val("Electric Train item name", p.get("item"), "electric_train")

# Electric Scooter > Scooter
p = parse_activity_text("I rode an Electric Scooter")
assert_val("Electric Scooter item name", p.get("item"), "electric_scooter")

# Chicken Biriyani > Chicken
p = parse_activity_text("I ate Chicken Biriyani")
assert_val("Chicken Biriyani item name", p.get("item"), "Chicken Biriyani")

# Mutton Biriyani > Mutton
p = parse_activity_text("I ate Mutton Biriyani")
assert_val("Mutton Biriyani item name", p.get("item"), "Mutton Biriyani")

# Sambar Rice > Rice
p = parse_activity_text("I ate Sambar Rice")
assert_val("Sambar Rice item name", p.get("item"), "Sambar Rice")

# Plastic Waste > Waste
p = parse_activity_text("I disposed 2 kg plastic waste")
assert_val("Plastic Waste item name", p.get("item"), "plastic_waste")

# Battery Waste > Waste
p = parse_activity_text("I disposed 1 kg battery waste")
assert_val("Battery Waste item name", p.get("item"), "battery_waste")

# E-Waste > Waste
p = parse_activity_text("I disposed 5 kg e-waste")
assert_val("E-Waste item name", p.get("item"), "e_waste")


# 2. ENERGY TESTS
print("\n--- ENERGY TESTS ---")
# Laptop Charger 135W 90 mins -> 0.17 kg
p = parse_activity_text("Laptop Charger\n135W\n90 mins")
co2, meta = calculate_emissions(db, p)
assert_val("Laptop Charger parsed item", p.get("item"), "laptop_charger")
assert_val("Laptop Charger parsed duration", p.get("duration"), 1.5)
assert_val("Laptop Charger parsed quantity (wattage flow count)", p.get("quantity"), 1.5)
assert_approx("Laptop Charger 135W 90 mins CO2", co2, 0.17)

# Fan 75W 8 hours -> 0.49 kg
p = parse_activity_text("Fan\n75W\n8 hours")
co2, meta = calculate_emissions(db, p)
assert_approx("Fan 75W 8 hours CO2", co2, 0.49)

# AC 1500W 3 hours -> 3.69 kg
p = parse_activity_text("AC\n1500W\n3 hours")
co2, meta = calculate_emissions(db, p)
assert_approx("AC 1500W 3 hours CO2", co2, 3.69)


# 3. TRANSPORT TESTS
print("\n--- TRANSPORT TESTS ---")
# 25 km Electric Train -> 0.50 kg
p = parse_activity_text("25 km Electric Train")
co2, meta = calculate_emissions(db, p)
assert_approx("25 km Electric Train CO2", co2, 0.50)

# 15 km Electric Scooter -> 0.23 kg
p = parse_activity_text("15 km Electric Scooter")
co2, meta = calculate_emissions(db, p)
assert_approx("15 km Electric Scooter CO2", co2, 0.23)

# 20 km Petrol Car -> 3.84 kg
p = parse_activity_text("20 km Petrol Car")
co2, meta = calculate_emissions(db, p)
assert_approx("20 km Petrol Car CO2", co2, 3.84)


# 4. FOOD TESTS
print("\n--- FOOD TESTS ---")
p = parse_activity_text("Chicken Biriyani")
assert_val("Chicken Biriyani food name", p.get("item"), "Chicken Biriyani")
co2, meta = calculate_emissions(db, p)
assert_approx("Chicken Biriyani CO2", co2, 2.50)

p = parse_activity_text("Sambar Rice")
assert_val("Sambar Rice food name", p.get("item"), "Sambar Rice")
co2, meta = calculate_emissions(db, p)
assert_approx("Sambar Rice CO2", co2, 0.45)


# 5. UNKNOWN TESTS
print("\n--- UNKNOWN TESTS ---")
# Yoga must remain Yoga
p = parse_activity_text("Yoga")
assert_val("Yoga item name", p.get("item"), "yoga")
assert_val("Yoga category", p.get("category"), "exercise")

# Quantum Engine must return Unknown
p = parse_activity_text("Quantum Engine")
assert_val("Quantum Engine item name", p.get("item"), "Unknown")
co2, meta = calculate_emissions(db, p)
assert_val("Quantum Engine CO2", co2, 0.0)

print("\n===============================")
if failures:
    print(f"FAILED {len(failures)} SPRINT TESTS")
    sys.exit(1)
else:
    print("ALL SPRINT TESTS PASSED")
    sys.exit(0)
