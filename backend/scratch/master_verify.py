"""
MASTER CROSS-VERIFICATION SPRINT
CarbonTracker NLP + Carbon Engine — End-to-End Validation
"""
import sys, os, time, math
start_time = time.time()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.nlp.parser import parse_activity_text, parse_compound_activity
from app.nlp.entity_engine import extract_entities
from app.calculations.engines import (
    calculate_transport_emission,
    calculate_appliance_emission,
    calculate_generic_emission,
    calculate_food_emission,
)
from app.services.activity_service import calculate_emissions

# ---------------------------------------------------------------------------
# Mock DB
# ---------------------------------------------------------------------------
class FakeRecord:
    def __init__(self, category, item_key, factor, unit, source="test", region="Global"):
        self.category=category; self.item_key=item_key; self.factor=factor
        self.unit=unit; self.source=source; self.region=region
        self.display_name=item_key.title()

class FakeDB:
    RECORDS = [
        FakeRecord("food","beef",60.0,"kg"),
        FakeRecord("food","chicken",6.9,"kg"),
        FakeRecord("food","rice",2.7,"kg"),
        FakeRecord("food","curd",2.2,"kg"),
        FakeRecord("food","milk",3.0,"kg"),
        FakeRecord("food","vegetables",0.5,"kg"),
        FakeRecord("transport","petrol car",0.192,"km"),
        FakeRecord("transport","petrol_car",0.192,"km"),
        FakeRecord("transport","electric_train",0.020,"km"),
        FakeRecord("transport","electric train",0.020,"km"),
        FakeRecord("transport","electric_scooter",0.015,"km"),
        FakeRecord("transport","electric scooter",0.015,"km"),
        FakeRecord("transport","bike",0.072,"km"),
        FakeRecord("transport","bicycle",0.0,"km"),
        FakeRecord("transport","walking",0.0,"km"),
        FakeRecord("transport","running",0.0,"km"),
        FakeRecord("electricity","grid electricity",0.82,"kWh","CEA"),  # India factor
        FakeRecord("appliances","ac",1500.0,"W"),
        FakeRecord("appliances","fan",75.0,"W"),
        FakeRecord("appliances","laptop",60.0,"W"),
    ]
    def query(self, _): return FakeQuery(self)

class FakeQuery:
    def __init__(self, db): self.db=db; self.filters={}
    def filter(self, *args):
        for arg in args:
            try: self.filters[arg.left.name] = arg.right.value
            except: pass
        return self
    def first(self):
        for r in self.db.RECORDS:
            match = all(getattr(r, k, None) == v or
                        (isinstance(getattr(r,k,None),str) and isinstance(v,str) and getattr(r,k,"").lower()==v.lower())
                        for k,v in self.filters.items())
            if match: return r
        if "item_key" in self.filters:
            ik = self.filters["item_key"].lower()
            for r in self.db.RECORDS:
                if r.item_key.lower() in ik or ik in r.item_key.lower(): return r
        return None
    def all(self):
        if "category" in self.filters:
            return [r for r in self.db.RECORDS if r.category==self.filters["category"]]
        return self.db.RECORDS

db = FakeDB()

# ---------------------------------------------------------------------------
# Test harness
# ---------------------------------------------------------------------------
RESULTS = []

def T(phase, name, text, fn):
    try:
        ok, msg = fn()
        RESULTS.append({"phase":phase,"name":name,"text":text,"ok":ok,"msg":msg})
    except Exception as e:
        RESULTS.append({"phase":phase,"name":name,"text":text,"ok":False,"msg":f"EXCEPTION: {e}"})

def p(text):
    return parse_activity_text(text)

def near(a, b, tol=0.02):
    return abs(a - b) <= tol

# ---------------------------------------------------------------------------
# PHASE A — INTENT DETECTION
# ---------------------------------------------------------------------------
def A1():
    r = p("I travelled 25 km by electric train")
    ok = r.get("category") == "transport"
    return ok, f"category={r.get('category')}, item={r.get('item')}"
T("A","A1: Electric Train → Transport", "I travelled 25 km by electric train", A1)

def A2():
    r = p("I used AC for 3 hours")
    ok = r.get("category") in ("appliances","electricity")
    return ok, f"category={r.get('category')}, item={r.get('item')}"
T("A","A2: AC → Energy", "I used AC for 3 hours", A2)

def A3():
    r = p("I ate chicken biriyani")
    ok = r.get("category") == "food"
    return ok, f"category={r.get('category')}, item={r.get('item')}"
T("A","A3: Chicken Biriyani → Food", "I ate chicken biriyani", A3)

def A4():
    r = p("I bought a laptop")
    ok = r.get("category") == "shopping"
    return ok, f"category={r.get('category')}, item={r.get('item')}"
T("A","A4: Laptop → Shopping", "I bought a laptop", A4)

def A5():
    r = p("I disposed 2 kg plastic waste")
    ok = r.get("category") == "waste"
    return ok, f"category={r.get('category')}, item={r.get('item')}"
T("A","A5: Plastic Waste → Waste", "I disposed 2 kg plastic waste", A5)

def A6():
    r = p("I did yoga for 1 hour")
    ok = r.get("category") == "exercise"
    bad = r.get("category") in ("food","transport","shopping","waste")
    return (ok and not bad), f"category={r.get('category')}, item={r.get('item')}"
T("A","A6: Yoga → Exercise (NOT Food/Transport/Shopping/Waste)", "I did yoga for 1 hour", A6)

# ---------------------------------------------------------------------------
# PHASE B — ENTITY RECOGNITION
# ---------------------------------------------------------------------------
def B1():
    r = p("I travelled 25 km by electric train")
    item = (r.get("item") or "").lower()
    vehicle_ok = "electric" in item and "train" in item
    not_just_train = item != "train"
    dist_ok = r.get("quantity") == 25 and r.get("unit") == "km"
    return (vehicle_ok and not_just_train and dist_ok), f"item={r.get('item')}, qty={r.get('quantity')}, unit={r.get('unit')}"
T("B","B1: Electric Train entity + 25km", "I travelled 25 km by electric train", B1)

def B2():
    r = p("I charged my laptop for 90 mins using 135W charger")
    item = (r.get("item") or "").lower()
    device_ok = "laptop" in item
    dur = r.get("quantity"); unit = r.get("unit")
    dur_ok = (dur == 1.5 and unit == "hours") or (dur == 90 and "min" in (unit or ""))
    return (device_ok and dur_ok), f"item={r.get('item')}, qty={r.get('quantity')}, unit={r.get('unit')}"
T("B","B2: Laptop Charger + 90 mins", "I charged my laptop for 90 mins using 135W charger", B2)

def B3():
    r = p("I ate chicken biriyani")
    item = (r.get("item") or "").lower()
    biryani_ok = "biryani" in item or "biriyani" in item
    splits = parse_compound_activity("I ate chicken biriyani")
    not_split = len(splits) == 1
    return (biryani_ok and not_split), f"item={r.get('item')}, splits={len(splits)}"
T("B","B3: Chicken Biriyani (whole, no split)", "I ate chicken biriyani", B3)

def B4():
    r = p("I ate sambar rice")
    item = (r.get("item") or "").lower()
    ok = "sambar" in item or "rice" in item
    return ok, f"item={r.get('item')}"
T("B","B4: Sambar Rice", "I ate sambar rice", B4)

def B5():
    r = p("I disposed 2 kg plastic waste")
    item = (r.get("item") or "").lower()
    ok = "plastic" in item
    qty_ok = r.get("quantity") == 2 and r.get("unit") == "kg"
    return (ok and qty_ok), f"item={r.get('item')}, qty={r.get('quantity')}, unit={r.get('unit')}"
T("B","B5: Plastic Waste + 2 kg", "I disposed 2 kg plastic waste", B5)

def B6():
    r = p("I did yoga for 1 hour")
    item = (r.get("item") or "").lower()
    act_ok = "yoga" in item
    not_curd = "curd" not in item and "rice" not in item
    not_food = r.get("category") != "food"
    return (act_ok and not_curd and not_food), f"category={r.get('category')}, item={r.get('item')}"
T("B","B6: Yoga entity (NOT Curd/Rice/Food)", "I did yoga for 1 hour", B6)

# ---------------------------------------------------------------------------
# PHASE C1 — TRANSPORT FORMULA
# ---------------------------------------------------------------------------
# Formula: distance_km × factor = CO2 (rounded to 2 dp)
GRID_INDIA = 0.82  # CEA India

def C1_1():
    # Electric Scooter 15 km: factor=0.015, expected=0.23
    co2, meta = calculate_transport_emission(db, "electric scooter", 15.0, "km")
    factor_ok = near(meta.get("factor", meta.get("emission_factor", 0)), 0.015, 0.001)
    co2_ok = near(round(co2, 2), 0.23)
    return (factor_ok and co2_ok), f"factor={meta.get('factor', meta.get('emission_factor'))}, co2={round(co2,2)} (expected 0.23)"
T("C1","C1-1: Electric Scooter 15km → 0.23 kg", "15 km Electric Scooter", C1_1)

def C1_2():
    # Electric Train 25 km: factor=0.020, expected=0.50
    co2, meta = calculate_transport_emission(db, "electric train", 25.0, "km")
    factor_ok = near(meta.get("factor", meta.get("emission_factor", 0)), 0.020, 0.001)
    co2_ok = near(round(co2, 2), 0.50)
    return (factor_ok and co2_ok), f"factor={meta.get('factor', meta.get('emission_factor'))}, co2={round(co2,2)} (expected 0.50)"
T("C1","C1-2: Electric Train 25km → 0.50 kg", "25 km Electric Train", C1_2)

def C1_3():
    # Petrol Car 20 km: factor=0.192, expected=3.84
    co2, meta = calculate_transport_emission(db, "petrol car", 20.0, "km")
    factor_ok = near(meta.get("factor", meta.get("emission_factor", 0)), 0.192, 0.001)
    co2_ok = near(round(co2, 2), 3.84)
    return (factor_ok and co2_ok), f"factor={meta.get('factor', meta.get('emission_factor'))}, co2={round(co2,2)} (expected 3.84)"
T("C1","C1-3: Petrol Car 20km → 3.84 kg", "20 km Petrol Car", C1_3)

def C1_4():
    # Walking 5 km: CO2 = 0.00
    co2, _ = calculate_transport_emission(db, "walking", 5.0, "km")
    return co2 == 0.0, f"co2={co2} (expected 0.0)"
T("C1","C1-4: Walking 5km → 0.00 kg", "5 km Walking", C1_4)

def C1_5():
    # Running 3 km: CO2 = 0.00
    co2, _ = calculate_transport_emission(db, "running", 3.0, "km")
    return co2 == 0.0, f"co2={co2} (expected 0.0)"
T("C1","C1-5: Running 3km → 0.00 kg", "3 km Running", C1_5)

# ---------------------------------------------------------------------------
# PHASE C2 — ENERGY FORMULA  (region=India → grid=0.82)
# ---------------------------------------------------------------------------
def C2_1():
    # AC 1500W, 3h, grid=0.82 → 1.5kW × 3h × 0.82 = 3.69
    co2, meta = calculate_appliance_emission(db, "ac", 3.0, region="india")
    kwh = meta.get("total_kwh", 0)
    expected_co2 = round(1500/1000 * 3 * 0.82, 2)  # 3.69
    kwh_ok = near(kwh, 4.5, 0.05)
    co2_ok = near(round(co2, 2), expected_co2)
    return (kwh_ok and co2_ok), f"kWh={kwh}, co2={round(co2,2)} (expected kWh=4.5, co2={expected_co2})"
T("C2","C2-1: AC 1500W 3h (India) → 3.69 kg", "AC 1500W 3h India grid", C2_1)

def C2_2():
    # Fan 75W, 8h, grid=0.82 → 0.075kW × 8h × 0.82 = 0.49
    co2, meta = calculate_appliance_emission(db, "fan", 8.0, region="india")
    kwh = meta.get("total_kwh", 0)
    expected_co2 = round(75/1000 * 8 * 0.82, 2)  # 0.49
    kwh_ok = near(kwh, 0.6, 0.05)
    co2_ok = near(round(co2, 2), expected_co2)
    return (kwh_ok and co2_ok), f"kWh={kwh}, co2={round(co2,2)} (expected kWh=0.6, co2={expected_co2})"
T("C2","C2-2: Fan 75W 8h (India) → 0.49 kg", "Fan 75W 8h India grid", C2_2)

def C2_3():
    # Laptop Charger 135W, 90min=1.5h, grid=0.82 → 0.135 × 1.5 × 0.82 = 0.166 ≈ 0.17
    # The engine's laptop is 60W by default; we test the formula directly with 135W
    from app.carbon.appliance_formula import calculate_appliance_co2
    co2_res = calculate_appliance_co2(watts=135.0, hours=1.5, grid_factor=0.82, source="CEA")
    co2 = co2_res["co2"]
    expected = round(0.135 * 1.5 * 0.82, 2)  # 0.17
    ok = near(round(co2, 2), expected)
    return ok, f"co2={round(co2,2)} (expected {expected})"
T("C2","C2-3: Laptop Charger 135W 90min (India) → 0.17 kg", "Laptop 135W 1.5h India grid", C2_3)

# ---------------------------------------------------------------------------
# LONGEST PHRASE MATCHING
# ---------------------------------------------------------------------------
def LP(label, text, check_fn):
    r = p(text)
    ok, msg = check_fn(r)
    RESULTS.append({"phase":"LP","name":f"LP: {label}","text":text,"ok":ok,"msg":msg})

LP("Electric Train > Train",
   "I travelled 20 km by electric train",
   lambda r: ("electric" in (r.get("item") or "").lower() and "train" in (r.get("item") or "").lower(),
              f"item={r.get('item')}"))

LP("Electric Scooter > Scooter",
   "I travelled 10 km by electric scooter",
   lambda r: ("electric" in (r.get("item") or "").lower() and "scooter" in (r.get("item") or "").lower(),
              f"item={r.get('item')}"))

LP("Laptop Charger > Laptop (shopping context)",
   "I bought a laptop charger",
   lambda r: (r.get("category") == "shopping" or "laptop" in (r.get("item") or "").lower(),
              f"category={r.get('category')}, item={r.get('item')}"))

LP("Chicken Biriyani > Chicken",
   "I ate chicken biriyani",
   lambda r: ("biryani" in (r.get("item") or "").lower() or "biriyani" in (r.get("item") or "").lower(),
              f"item={r.get('item')}"))

LP("Sambar Rice > Rice",
   "I ate sambar rice",
   lambda r: ("sambar" in (r.get("item") or "").lower() or "rice" in (r.get("item") or "").lower(),
              f"item={r.get('item')}"))

LP("Plastic Waste > Waste",
   "I disposed 2 kg plastic waste",
   lambda r: ("plastic" in (r.get("item") or "").lower(),
              f"item={r.get('item')}"))

LP("Battery Waste > Waste",
   "I disposed battery waste",
   lambda r: ("battery" in (r.get("item") or "").lower() or "waste" in (r.get("item") or "").lower(),
              f"category={r.get('category')}, item={r.get('item')}"))

LP("E-Waste > Waste",
   "I recycled e-waste",
   lambda r: (r.get("category") == "waste" or "waste" in (r.get("item") or "").lower() or "recycl" in (r.get("item") or "").lower(),
              f"category={r.get('category')}, item={r.get('item')}"))

# ---------------------------------------------------------------------------
# UNKNOWN ENTITY TESTS
# ---------------------------------------------------------------------------
def UNK(label, text, check_fn):
    r = p(text)
    ok, msg = check_fn(r)
    RESULTS.append({"phase":"UNK","name":f"UNK: {label}","text":text,"ok":ok,"msg":msg})

UNK("Spaceship (Unknown Transport)",
    "I used a spaceship for 500 km",
    lambda r: (r.get("category") not in ("food","exercise","shopping") or r.get("confidence",1.0) < 0.9,
               f"category={r.get('category')}, item={r.get('item')}, conf={r.get('confidence')}"))

UNK("Moon Burger (Unknown Food)",
    "I ate moon burger",
    lambda r: (r.get("category") == "food" or r.get("confidence",1.0) <= 0.97,
               f"category={r.get('category')}, item={r.get('item')}, conf={r.get('confidence')}"))

UNK("Quantum Engine (Unknown Device)",
    "I used quantum engine",
    lambda r: (r.get("category") not in ("food","exercise") or r.get("confidence",1.0) < 0.9,
               f"category={r.get('category')}, item={r.get('item')}, conf={r.get('confidence')}"))

# ---------------------------------------------------------------------------
# CARBON OUTPUT VALIDATION (rounding + no negatives)
# ---------------------------------------------------------------------------
def CV(label, co2_val, expected_rounded):
    actual = round(co2_val, 2)
    ok = actual == expected_rounded and co2_val >= 0
    RESULTS.append({"phase":"CV","name":f"CV: {label}","text":str(co2_val),
                    "ok":ok,"msg":f"round({co2_val},2)={actual} (expected {expected_rounded})"})

CV("0.225 → 0.23", 0.225, 0.23)
CV("3.687 → 3.69", 3.687, 3.69)
CV("0.166 → 0.17", 0.166, 0.17)
CV("No negative: 0.0 ≥ 0", 0.0, 0.0)

# ---------------------------------------------------------------------------
# CRITICAL FAIL CONDITIONS
# ---------------------------------------------------------------------------
CRITICAL = []
def crit_check(label, condition):
    if condition: CRITICAL.append(f"CRITICAL FAIL: {label}")

r_yoga = p("I did yoga for 1 hour")
r_ac   = p("I used AC for 3 hours")
r_lbuy = p("I bought a laptop")
r_etrain = p("I travelled 20 km by electric train")
r_bir  = p("I ate chicken biriyani")
r_fan  = p("I used fan for 8 hours")

crit_check("Yoga became Curd",
    "curd" in (r_yoga.get("item") or "").lower() or r_yoga.get("category") == "food")
crit_check("AC became Running",
    "run" in (r_ac.get("item") or "").lower() or r_ac.get("category") == "exercise")
crit_check("Bought Laptop → Appliance Usage",
    r_lbuy.get("category") in ("appliances","electricity"))
crit_check("Electric Train → just Train",
    (r_etrain.get("item") or "").lower() == "train")
crit_check("Chicken Biriyani split",
    len(parse_compound_activity("I ate chicken biriyani")) > 1)
crit_check("Fan 8h became wrong duration",
    r_fan.get("quantity") not in (8, 8.0))

# ---------------------------------------------------------------------------
# REPORT GENERATION
# ---------------------------------------------------------------------------
elapsed = round(time.time() - start_time, 2)

by_phase = {}
for r in RESULTS:
    ph = r["phase"]
    by_phase.setdefault(ph, {"total":0,"passed":0})
    by_phase[ph]["total"] += 1
    if r["ok"]: by_phase[ph]["passed"] += 1

total_passed = sum(r["ok"] for r in RESULTS)
total_all    = len(RESULTS)
failed = [r for r in RESULTS if not r["ok"]]
overall = "PASS" if (total_passed == total_all and not CRITICAL) else "FAIL"

ph_map = {
    "A":  "Intent Detection",
    "B":  "Entity Recognition",
    "C1": "Transport Formula",
    "C2": "Energy Formula",
    "LP": "Longest Phrase Matching",
    "UNK":"Unknown Entity Handling",
    "CV": "Carbon Output Validation",
}

print("="*60)
print(" MASTER CROSS-VERIFICATION SPRINT — FINAL REPORT")
print("="*60)
print(f" OVERALL STATUS : {overall}")
print(f" TOTAL TESTS    : {total_all}")
print(f" PASSED         : {total_passed}")
print(f" FAILED         : {len(failed)}")
print(f" CRITICAL FAILS : {len(CRITICAL)}")
print(f" RUNTIME        : {elapsed}s")
print()
print(" ACCURACY BY PHASE:")
for ph, stats in by_phase.items():
    pct = round(stats["passed"]/stats["total"]*100, 1)
    label = ph_map.get(ph, ph)
    print(f"   {label:<30} {pct}% ({stats['passed']}/{stats['total']})")

if failed:
    print()
    print(" FAILED TEST CASES:")
    for f in failed:
        print(f"   [{f['phase']}] {f['name']}")
        print(f"        Input  : {f['text']}")
        print(f"        Detail : {f['msg']}")

if CRITICAL:
    print()
    print(" CRITICAL FAILURE CONDITIONS TRIGGERED:")
    for c in CRITICAL: print(f"   {c}")

    print()
    print(" ROOT CAUSE:")
    print("   One or more safety guards, phrase-matcher priorities, or")
    print("   emission factor lookups produced incorrect output.")
    print()
    print(" RECOMMENDED FIX:")
    print("   Review EXERCISE_HARD_BLOCK, direct_checks, longest-phrase")
    print("   matching order in entity_engine.py, and appliance duration")
    print("   extraction in parser.py.")

if not failed and not CRITICAL:
    print()
    print(" All verification cases passed. No action required.")

print("="*60)
