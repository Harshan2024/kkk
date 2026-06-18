"""Fix Verification: Duration (90 mins = 1.5h) + Grid factor (always 0.82)"""
import sys
sys.path.insert(0, '.')

from app.nlp.entity_engine import normalize_units_in_text
from app.nlp.parser import parse_activity_text
from app.carbon.appliance_formula import calculate_appliance_co2
from app.carbon.appliance_factors import MANDATORY_GRID_FACTOR, GRID_FACTORS

def ok(flag): return "PASS" if flag else "FAIL"
results = []

# -- FIX 1: Duration Extraction -----------------------------------------------
print("=" * 60)
print(" FIX 1: Duration Extraction (mins -> hours)")
print("=" * 60)

cases = [
    ("I used laptop charger for 90 mins", 1.5,  "hours"),
    ("I used fan for 30 mins",            0.5,  "hours"),
    ("I used AC for 3 hours",             3.0,  "hours"),
    ("I used AC for 90 mins",             1.5,  "hours"),
    ("I used laptop for 120 mins",        2.0,  "hours"),
    ("I used water heater for 45 mins",   0.75, "hours"),
]

for text, expected_qty, expected_unit in cases:
    normed = normalize_units_in_text(text)
    r      = parse_activity_text(text)
    qty    = r.get("quantity", 0)
    unit   = r.get("unit", "")
    passed = abs(qty - expected_qty) < 0.001 and unit == expected_unit
    results.append(passed)
    print(f"  [{ok(passed)}] {text}")
    print(f"         normalized : {normed}")
    print(f"         qty={qty} unit={unit}  (expected {expected_qty} {expected_unit})")

# ── FIX 2: Grid Factor ───────────────────────────────────────────────────────
print()
print("=" * 60)
print(" FIX 2: Energy Formula = (W/1000) x Hours x 0.82")
print("=" * 60)

# Approved examples from Section B
formula_cases = [
    ("Laptop Charger 135W 1.5h",  135.0, 1.5, 0.82, 0.17),
    ("AC 1500W 3h",               1500.0, 3.0, 0.82, 3.69),
    ("Fan 75W 8h",                75.0,  8.0, 0.82, 0.49),
]
for label, w, h, gf, expected in formula_cases:
    res  = calculate_appliance_co2(w, h, gf, "CarbonTracker Standard")
    co2  = round(res["co2"], 2)
    fact = res["factor"]
    p = abs(co2 - expected) < 0.01 and fact == 0.82
    results.append(p)
    print(f"  [{ok(p)}] {label}")
    print(f"         ({w}/1000) x {h} x {gf} = {expected} kg  (got {co2}, factor={fact})")

# Constant guards
p4 = (MANDATORY_GRID_FACTOR == 0.82)
p5 = all(v["factor"] == 0.82 for v in GRID_FACTORS.values())
results += [p4, p5]
print(f"  [{ok(p4)}] MANDATORY_GRID_FACTOR == 0.82  (got {MANDATORY_GRID_FACTOR})")
print(f"  [{ok(p5)}] All GRID_FACTORS entries == 0.82")

print()
overall = "PASS" if all(results) else "FAIL"
print(f" OVERALL : {overall}  ({sum(results)}/{len(results)} checks)")
print("=" * 60)
