"""
stabilization_sprint.py
=======================
CarbonTracker AI - Stabilization Sprint
Verifies Food and Waste Engines before Phase D.

Issues Covered:
    Issue 1: Alias mapping "electronic waste" -> E-Waste
    Issue 2: Food factor report (14 mandatory foods)
    Issue 3: Waste factor report (8 mandatory waste types)
    Issue 4: Entity display correctness (E-Waste, not "Recycling")
    Issue 5: Formula verification report (food + waste)
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.carbon.waste_carbon_engine import calculate_waste_carbon_from_text
from app.carbon.food_carbon_engine import calculate_food_carbon_from_text
from app.carbon.waste_factors import WASTE_FACTORS, get_waste_factor
from app.carbon.food_factors import FOOD_FACTORS, get_food_factor
from app.carbon.waste_formula import calculate_waste_carbon, format_waste_formula
from app.carbon.food_formula import calculate_food_carbon, format_food_formula

PASS_COUNT = 0
FAIL_COUNT = 0

def check(label, actual, expected):
    global PASS_COUNT, FAIL_COUNT
    ok = (actual == expected)
    status = "PASS" if ok else "FAIL"
    if ok:
        PASS_COUNT += 1
        print(f"  [{status}] {label}: {actual!r}")
    else:
        FAIL_COUNT += 1
        print(f"  [{status}] {label}: got {actual!r}, expected {expected!r}")


# =============================================================================
# ISSUE 1: Alias Mapping Verification
# =============================================================================
print("\n" + "=" * 70)
print(" ISSUE 1 — Alias Mapping: 'electronic waste' -> E-Waste")
print("=" * 70)

r = calculate_waste_carbon_from_text("I recycled 1 kg electronic waste")
check("waste_type",  r.get("waste_type"),  "E-Waste")
check("weight",      r.get("weight"),      1.0)
check("factor",      r.get("factor"),      12.0)
check("carbon",      r.get("carbon"),      12.0)
check("no error",    r.get("error"),       None)


# =============================================================================
# ISSUE 2: Food Factor Report
# =============================================================================
print("\n" + "=" * 70)
print(" ISSUE 2 — Food Factor Report (values from food_factors.py only)")
print("=" * 70)

FOOD_FACTOR_EXPECTED = {
    "chicken biriyani": 2.50,
    "mutton biriyani":  3.50,
    "egg rice":         0.80,
    "egg noodles":      0.85,
    "veg noodles":      0.50,
    "dosa":             0.18,
    "idli":             0.12,
    "sambar rice":      0.45,
    "rasam rice":       0.35,
    "curd rice":        0.40,
    "coffee":           0.08,
    "tea":              0.05,
    "cake":             0.40,
    "chocolate":        0.25,
}

print(f"\n  {'Food Item':<25} {'Expected':>10} {'Actual':>10} {'Status':>8}")
print("  " + "-" * 60)
for food, expected_factor in FOOD_FACTOR_EXPECTED.items():
    actual = get_food_factor(food)
    ok = (actual == expected_factor)
    status = "PASS" if ok else "FAIL"
    if ok:
        PASS_COUNT += 1
    else:
        FAIL_COUNT += 1
    print(f"  {food:<25} {expected_factor:>10.2f} {(actual or 'MISSING'):>10} {('['+status+']'):>8}")


# =============================================================================
# ISSUE 3: Waste Factor Report
# =============================================================================
print("\n" + "=" * 70)
print(" ISSUE 3 — Waste Factor Report (values from waste_factors.py only)")
print("=" * 70)

WASTE_FACTOR_EXPECTED = {
    "plastic waste":  6.0,
    "paper waste":    1.3,
    "organic waste":  0.5,
    "food waste":     0.8,
    "e-waste":        12.0,
    "battery waste":  15.0,
    "glass waste":    0.9,
    "metal waste":    2.1,
}

print(f"\n  {'Waste Type':<25} {'Expected':>10} {'Actual':>10} {'Status':>8}")
print("  " + "-" * 60)
for waste, expected_factor in WASTE_FACTOR_EXPECTED.items():
    actual = get_waste_factor(waste)
    ok = (actual == expected_factor)
    status = "PASS" if ok else "FAIL"
    if ok:
        PASS_COUNT += 1
    else:
        FAIL_COUNT += 1
    print(f"  {waste:<25} {expected_factor:>10.1f} {(actual or 'MISSING'):>10} {('['+status+']'):>8}")


# =============================================================================
# ISSUE 4: UI Entity Display Correctness
# =============================================================================
print("\n" + "=" * 70)
print(" ISSUE 4 — Entity Display: must show detected entity, not action verb")
print("=" * 70)

ENTITY_DISPLAY_CASES = [
    ("I recycled 1 kg e-waste",             "E-Waste"),
    ("I recycled 1 kg electronic waste",    "E-Waste"),
    ("I disposed 2 kg plastic waste",       "Plastic Waste"),
    ("I disposed 500 g paper waste",        "Paper Waste"),
    ("I disposed 3 kg organic waste",       "Organic Waste"),
    ("I disposed 1 kg battery waste",       "Battery Waste"),
    ("I disposed 1 kg glass waste",         "Glass Waste"),
    ("I disposed 1 kg metal waste",         "Metal Waste"),
    ("I disposed 1 kg food waste",          "Food Waste"),
]

print()
for text, expected_entity in ENTITY_DISPLAY_CASES:
    r = calculate_waste_carbon_from_text(text)
    actual_entity = r.get("waste_type")
    ok = (actual_entity == expected_entity)
    status = "PASS" if ok else "FAIL"
    if ok:
        PASS_COUNT += 1
    else:
        FAIL_COUNT += 1
    print(f"  [{status}] '{text}'")
    print(f"         waste_type: got {actual_entity!r}, expected {expected_entity!r}")


# =============================================================================
# ISSUE 5: Formula Verification Report
# =============================================================================
print("\n" + "=" * 70)
print(" ISSUE 5A — Waste Formula Verification Report")
print("=" * 70)

WASTE_FORMULA_CASES = [
    ("plastic waste",  2.0,  6.0,  "2 x 6.0",   12.0),
    ("e-waste",        1.0, 12.0,  "1 x 12.0",  12.0),
    ("organic waste",  3.0,  0.5,  "3 x 0.5",    1.5),
    ("paper waste",    0.5,  1.3,  "0.5 x 1.3",  0.65),
    ("battery waste",  2.0, 15.0,  "2 x 15.0",  30.0),
    ("glass waste",    1.0,  0.9,  "1 x 0.9",    0.9),
    ("metal waste",    1.0,  2.1,  "1 x 2.1",    2.1),
    ("food waste",     1.0,  0.8,  "1 x 0.8",    0.8),
]

print(f"\n  {'Waste Type':<18} {'Weight':>6} {'Factor':>7} {'Formula':<14} {'Expected CO2':>12} {'Actual CO2':>10} {'Status':>8}")
print("  " + "-" * 85)
for waste_type, weight, factor, formula, expected_co2 in WASTE_FORMULA_CASES:
    actual_co2  = calculate_waste_carbon(weight, factor)
    actual_fmt  = format_waste_formula(weight, factor)
    ok_co2      = (actual_co2 == expected_co2)
    ok_formula  = (actual_fmt == formula)
    ok          = ok_co2 and ok_formula
    status      = "PASS" if ok else "FAIL"
    if ok:
        PASS_COUNT += 1
    else:
        FAIL_COUNT += 1
        if not ok_co2:
            print(f"    !! CO2 mismatch: got {actual_co2}, expected {expected_co2}")
        if not ok_formula:
            print(f"    !! Formula mismatch: got {actual_fmt!r}, expected {formula!r}")
    print(f"  {waste_type:<18} {weight:>6} {factor:>7} {formula:<14} {expected_co2:>12.2f} {actual_co2:>10.2f} {('['+status+']'):>8}")


print("\n" + "=" * 70)
print(" ISSUE 5B — Food Formula Verification Report")
print("=" * 70)

FOOD_FORMULA_CASES = [
    ("chicken biriyani", 1, 2.50, "1 x 2.50",  2.50),
    ("chicken biriyani", 2, 2.50, "2 x 2.50",  5.00),
    ("mutton biriyani",  1, 3.50, "1 x 3.50",  3.50),
    ("egg noodles",      1, 0.85, "1 x 0.85",  0.85),
    ("sambar rice",      1, 0.45, "1 x 0.45",  0.45),
    ("dosa",             3, 0.18, "3 x 0.18",  0.54),
    ("idli",             2, 0.12, "2 x 0.12",  0.24),
    ("rasam rice",       1, 0.35, "1 x 0.35",  0.35),
    ("curd rice",        1, 0.40, "1 x 0.40",  0.40),
    ("coffee",           2, 0.08, "2 x 0.08",  0.16),
    ("tea",              3, 0.05, "3 x 0.05",  0.15),
    ("cake",             1, 0.40, "1 x 0.40",  0.40),
    ("chocolate",        1, 0.25, "1 x 0.25",  0.25),
    ("veg noodles",      1, 0.50, "1 x 0.50",  0.50),
]

print(f"\n  {'Food Item':<20} {'Srv':>4} {'Factor':>7} {'Formula':<14} {'Expected CO2':>12} {'Actual CO2':>10} {'Status':>8}")
print("  " + "-" * 85)
for food_item, servings, factor, formula, expected_co2 in FOOD_FORMULA_CASES:
    actual_co2 = calculate_food_carbon(servings, factor)
    actual_fmt = format_food_formula(servings, factor)
    ok_co2     = (actual_co2 == expected_co2)
    ok_formula = (actual_fmt == formula)
    ok         = ok_co2 and ok_formula
    status     = "PASS" if ok else "FAIL"
    if ok:
        PASS_COUNT += 1
    else:
        FAIL_COUNT += 1
        if not ok_co2:
            print(f"    !! CO2 mismatch: got {actual_co2}, expected {expected_co2}")
        if not ok_formula:
            print(f"    !! Formula mismatch: got {actual_fmt!r}, expected {formula!r}")
    print(f"  {food_item:<20} {servings:>4} {factor:>7} {formula:<14} {expected_co2:>12.2f} {actual_co2:>10.2f} {('['+status+']'):>8}")


# =============================================================================
# FINAL SUMMARY
# =============================================================================
print("\n" + "=" * 70)
total = PASS_COUNT + FAIL_COUNT
print(f"  STABILIZATION SPRINT RESULTS")
print(f"  PASSED : {PASS_COUNT}")
print(f"  FAILED : {FAIL_COUNT}")
print(f"  TOTAL  : {total}")
overall = "ALL PASS" if FAIL_COUNT == 0 else "FAILURES DETECTED"
print(f"  STATUS : {overall}")
print("=" * 70)

sys.exit(1 if FAIL_COUNT > 0 else 0)
