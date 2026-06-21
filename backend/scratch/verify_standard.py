"""
CARBONTRACKER MASTER EMISSION FORMULA STANDARD — Post-Update Verification
Validates all five factor datasets and formula calculations.
"""
import sys, os, time
start = time.time()
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.carbon.transport_factors import TRANSPORT_FACTORS
from app.carbon.appliance_factors import APPLIANCE_WATTS, GRID_FACTORS
from app.carbon.food_factors       import FOOD_FACTORS
from app.carbon.shopping_factors   import SHOPPING_FACTORS
from app.carbon.waste_factors      import WASTE_FACTORS
from app.carbon.transport_formula  import calculate_transport_co2
from app.carbon.appliance_formula  import calculate_appliance_co2
from app.carbon.food_formula       import calculate_food_co2
from app.carbon.waste_formula      import calculate_waste_co2
from app.carbon.shopping_formula   import calculate_shopping_co2

RESULTS = []
def T(phase, name, ok, msg):
    RESULTS.append({"phase":phase,"name":name,"ok":ok,"msg":msg})
def near(a,b,tol=0.001): return abs(a-b)<=tol

# ── SECTION A: Transport Factors ────────────────────────────────────────────
transport_expected = {
    "petrol car": 0.192, "diesel car": 0.171, "cng car": 0.110,
    "hybrid car": 0.095, "electric car": 0.053,
    "motorcycle": 0.103, "bike": 0.103,
    "petrol scooter": 0.075, "electric scooter": 0.015, "electric bike": 0.020,
    "auto rickshaw": 0.090, "taxi": 0.192, "cab": 0.192,
    "bus": 0.105, "electric bus": 0.060,
    "train": 0.041, "electric train": 0.020, "metro": 0.020,
    "domestic flight": 0.255, "international flight": 0.195, "flight": 0.255,
    "ferry": 0.115, "passenger ship": 0.020,
    "walking": 0.0, "running": 0.0, "jogging": 0.0,
    "cycling": 0.0, "bicycle": 0.0,
}
for vehicle, expected in transport_expected.items():
    actual = TRANSPORT_FACTORS.get(vehicle, {}).get("factor", None)
    ok = actual is not None and near(actual, expected)
    T("A-Factors", f"Transport factor: {vehicle}", ok,
      f"expected={expected}, got={actual}")

# ── SECTION A: Transport Formula ─────────────────────────────────────────────
transport_formula_cases = [
    ("electric scooter", 15.0, 0.015, 0.23),
    ("electric train",   25.0, 0.020, 0.50),
    ("petrol car",       20.0, 0.192, 3.84),
    ("walking",           5.0, 0.000, 0.00),
    ("running",           3.0, 0.000, 0.00),
    ("motorcycle",        10.0, 0.103, 1.03),
    ("bus",               30.0, 0.105, 3.15),
    ("metro",             12.0, 0.020, 0.24),
]
for vehicle, dist, factor, expected_co2 in transport_formula_cases:
    res = calculate_transport_co2(dist, factor, "CarbonTracker Standard")
    co2 = round(res["co2"], 2)
    ok = near(co2, expected_co2, 0.01)
    T("A-Formula", f"Transport formula: {vehicle} {dist}km", ok,
      f"formula={dist}×{factor}={expected_co2}, got={co2}")

# ── SECTION B: Energy Grid Factor ────────────────────────────────────────────
for region, info in GRID_FACTORS.items():
    ok = near(info["factor"], 0.82)
    T("B-Factors", f"Grid factor [{region}]=0.82", ok,
      f"expected=0.82, got={info['factor']}")

# ── SECTION B: Energy Formula ────────────────────────────────────────────────
energy_cases = [
    ("AC",              1500.0, 3.0,  0.82, 3.69),
    ("Fan",             75.0,   8.0,  0.82, 0.49),
    ("Laptop Charger",  135.0,  1.5,  0.82, 0.17),
]
for label, watts, hours, gf, expected_co2 in energy_cases:
    res = calculate_appliance_co2(watts, hours, gf, "CarbonTracker Standard")
    co2 = round(res["co2"], 2)
    ok = near(co2, expected_co2, 0.01)
    kwh = round(watts / 1000 * hours, 4)
    T("B-Formula", f"Energy formula: {label} {watts}W {hours}h",ok,
      f"kWh={kwh}, {kwh}×{gf}={expected_co2}, got={co2}")

# ── SECTION C: Food Factors ──────────────────────────────────────────────────
food_expected = {
    "vegetable salad": 0.20, "idli": 0.12, "dosa": 0.18,
    "sambar rice": 0.45, "rasam rice": 0.35, "curd rice": 0.40,
    "egg rice": 0.80, "chicken rice": 1.60, "mutton rice": 3.00,
    "veg noodles": 0.50, "egg noodles": 0.85, "chicken noodles": 1.70,
    "chicken biryani": 2.50, "mutton biryani": 3.50,
    "tea": 0.05, "coffee": 0.08,
    "chocolate": 0.25, "cake": 0.40, "ice cream": 0.30,
    "candy": 0.05, "sweets": 0.20,
}
for dish, expected in food_expected.items():
    val = FOOD_FACTORS.get(dish)
    actual = val.get("factor") if isinstance(val, dict) else val
    ok = actual is not None and near(actual, expected)
    T("C-Factors", f"Food factor: {dish}", ok,
      f"expected={expected}, got={actual}")

# ── SECTION C: Food Formula ─────────────────────────────────────────────────
food_formula_cases = [
    ("chicken biryani", 1.0, 2.50, 2.50),
    ("sambar rice",     2.0, 0.45, 0.90),
    ("idli",            3.0, 0.12, 0.36),
    ("coffee",          1.0, 0.08, 0.08),
]
for dish, qty, factor, expected_co2 in food_formula_cases:
    res = calculate_food_co2(qty, factor, "CarbonTracker Standard")
    co2 = round(res["co2"], 2)
    ok = near(co2, expected_co2, 0.01)
    T("C-Formula", f"Food formula: {qty}×{dish}", ok,
      f"formula={qty}×{factor}={expected_co2}, got={co2}")

# ── SECTION D: Shopping Factors ──────────────────────────────────────────────
shopping_expected = {
    "laptop": 300.0, "smartphone": 70.0, "tablet": 100.0,
    "television": 350.0, "refrigerator": 400.0, "washing machine": 250.0,
    "bicycle": 120.0, "t-shirt": 5.0, "shirt": 6.0, "jeans": 25.0,
    "shoes": 15.0,
}
for item, expected in shopping_expected.items():
    actual = SHOPPING_FACTORS.get(item, {}).get("factor", None)
    ok = actual is not None and near(actual, expected)
    T("D-Factors", f"Shopping factor: {item}", ok,
      f"expected={expected}, got={actual}")

# ── SECTION D: Shopping Formula ──────────────────────────────────────────────
shopping_formula_cases = [
    ("laptop",      1, 300.0, 300.0),
    ("smartphone",  2, 70.0,  140.0),
    ("jeans",       3, 25.0,   75.0),
    ("t-shirt",     5, 5.0,   25.0),
]
for item, qty, factor, expected_co2 in shopping_formula_cases:
    res = calculate_shopping_co2(qty, factor, "CarbonTracker Standard")
    co2 = round(res["co2"], 2)
    ok = near(co2, expected_co2, 0.01)
    T("D-Formula", f"Shopping formula: {qty}×{item}", ok,
      f"formula={qty}×{factor}={expected_co2}, got={co2}")

# ── SECTION E: Waste Factors ─────────────────────────────────────────────────
waste_expected = {
    "plastic waste": 6.0, "e-waste": 12.0, "battery waste": 15.0,
    "organic waste": 0.5, "food waste": 0.8, "paper waste": 1.3,
    "glass waste": 0.9, "metal waste": 2.1,
}
for wtype, expected in waste_expected.items():
    val = WASTE_FACTORS.get(wtype)
    actual = val.get("factor") if isinstance(val, dict) else val
    ok = actual is not None and near(actual, expected)
    T("E-Factors", f"Waste factor: {wtype}", ok,
      f"expected={expected}, got={actual}")

# ── SECTION E: Waste Formula ─────────────────────────────────────────────────
waste_formula_cases = [
    ("plastic waste",   2.0,  6.0, 12.0),
    ("e-waste",         1.0, 12.0, 12.0),
    ("battery waste",   0.5, 15.0,  7.50),
    ("organic waste",  10.0,  0.5,  5.0),
    ("paper waste",     3.0,  1.3,  3.90),
]
for wtype, weight, factor, expected_co2 in waste_formula_cases:
    res = calculate_waste_co2(weight, factor, "CarbonTracker Standard")
    co2 = round(res["co2"], 2)
    ok = near(co2, expected_co2, 0.01)
    T("E-Formula", f"Waste formula: {weight}kg {wtype}", ok,
      f"formula={weight}×{factor}={expected_co2}, got={co2}")

# ── SECTION F: Rounding Validation ───────────────────────────────────────────
rounding_cases = [(0.225, 0.23), (0.166, 0.17), (3.687, 3.69), (0.492, 0.49)]
for val, expected in rounding_cases:
    actual = round(val, 2)
    ok = actual == expected
    T("F-Rounding", f"ROUND({val},2)={expected}", ok, f"got={actual}")

# ── SECTION F: No Negative Outputs ───────────────────────────────────────────
T("F-NoNeg", "All factors ≥ 0 (transport)", all((v.get("factor") if isinstance(v, dict) else v)>=0 for v in TRANSPORT_FACTORS.values() if v is not None), "")
T("F-NoNeg", "All factors ≥ 0 (food)",      all((v.get("factor") if isinstance(v, dict) else v)>=0 for v in FOOD_FACTORS.values() if v is not None), "")
T("F-NoNeg", "All factors ≥ 0 (waste)",     all((v.get("factor") if isinstance(v, dict) else v)>=0 for v in WASTE_FACTORS.values() if v is not None), "")
T("F-NoNeg", "All factors ≥ 0 (shopping)",  all((v.get("factor") if isinstance(v, dict) else v)>=0 for v in SHOPPING_FACTORS.values() if v is not None), "")

# ─────────────────────────────────────────────────────────────────────────────
# REPORT
# ─────────────────────────────────────────────────────────────────────────────
elapsed = round(time.time()-start, 2)
failed  = [r for r in RESULTS if not r["ok"]]
passed  = len(RESULTS)-len(failed)
status  = "PASS" if not failed else "FAIL"

by_phase = {}
for r in RESULTS:
    ph = r["phase"]
    by_phase.setdefault(ph,{"t":0,"p":0})
    by_phase[ph]["t"]+=1
    if r["ok"]: by_phase[ph]["p"]+=1

print("="*62)
print(" MASTER EMISSION FORMULA STANDARD — POST-UPDATE VERIFICATION")
print("="*62)
print(f" OVERALL   : {status}")
print(f" TOTAL     : {len(RESULTS)} tests  PASSED: {passed}  FAILED: {len(failed)}")
print(f" RUNTIME   : {elapsed}s")
print()
print(" PHASE SUMMARY:")
phase_labels = {
    "A-Factors":"Transport Factors",   "A-Formula":"Transport Formula",
    "B-Factors":"Grid Factor",         "B-Formula":"Energy Formula",
    "C-Factors":"Food Factors",        "C-Formula":"Food Formula",
    "D-Factors":"Shopping Factors",    "D-Formula":"Shopping Formula",
    "E-Factors":"Waste Factors",       "E-Formula":"Waste Formula",
    "F-Rounding":"Rounding Rules",     "F-NoNeg":"No-Negative Guard",
}
for ph,stats in by_phase.items():
    pct=round(stats["p"]/stats["t"]*100,1)
    label = phase_labels.get(ph, ph)
    bar = "OK" if pct==100 else "!!"
    print(f"   {bar} {label:<28} {pct:5.1f}%  ({stats['p']}/{stats['t']})")

if failed:
    print()
    print(" FAILED CASES:")
    for f in failed:
        print(f"   [{f['phase']}] {f['name']}")
        if f['msg']: print(f"            {f['msg']}")
    print()
    print(" ROOT CAUSE:")
    print("   Factor value(s) not matching the approved standard.")
    print(" RECOMMENDED FIX:")
    print("   Update the factor entries listed above to the approved values.")
else:
    print()
    print(" All factor datasets and formula calculations validated.")
    print(" CarbonTracker is now fully compliant with the")
    print(" Master Emission Formula Standard.")
print("="*62)
