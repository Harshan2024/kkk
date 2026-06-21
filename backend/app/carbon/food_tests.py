"""
food_tests.py
=============
CarbonTracker AI - Phase C3 Food Carbon Engine Verification Tests

Test Matrix (per specification):
    Test 1:  "I ate chicken biriyani"           -> Food=Chicken Biriyani,  Servings=1, CO2=2.50
    Test 2:  "I ate 2 chicken biriyani"         -> CO2=5.00
    Test 3:  "I ate mutton biriyani"            -> CO2=3.50
    Test 4:  "I ate sambar rice"                -> CO2=0.45
    Test 5:  "I ate egg noodles"                -> CO2=0.85
    Test 6:  "I ate 3 dosa"                     -> CO2=0.54
    Test 7:  "I ate moon burger"                -> {"error": "unknown_food_item"}
    Test 8:  "I ate chicken biriyani and egg noodles" -> Two entities, no splitting error

Plus additional verification:
    - Longest-phrase-first matching (chicken biriyani > chicken)
    - Textual number serving extraction ("three idli" -> 3)
    - All mandatory food factors present
    - Formula string format correctness
    - Performance benchmark
"""

import sys
import os
import time

# Ensure backend root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.carbon.food_carbon_engine import (
    calculate_food_carbon_from_text,
    extract_all_food_items,
)
from app.carbon.food_factors import FOOD_FACTORS, get_food_factor

PASS_COUNT = 0
FAIL_COUNT = 0


def check(label: str, actual, expected) -> bool:
    global PASS_COUNT, FAIL_COUNT
    ok = (actual == expected)
    status = "PASS" if ok else "FAIL"
    if ok:
        PASS_COUNT += 1
        print(f"  [{status}] {label}: {actual!r}")
    else:
        FAIL_COUNT += 1
        print(f"  [{status}] {label}: got {actual!r}, expected {expected!r}")
    return ok


def check_close(label: str, actual, expected, tol=0.001) -> bool:
    """Floating-point approx comparison."""
    global PASS_COUNT, FAIL_COUNT
    try:
        ok = abs(float(actual) - float(expected)) <= tol
    except (TypeError, ValueError):
        ok = False
    status = "PASS" if ok else "FAIL"
    if ok:
        PASS_COUNT += 1
        print(f"  [{status}] {label}: {actual!r} ~= {expected!r}")
    else:
        FAIL_COUNT += 1
        print(f"  [{status}] {label}: got {actual!r}, expected ~= {expected!r}")
    return ok


def run_tests():
    global PASS_COUNT, FAIL_COUNT

    print("=" * 75)
    print(" CarbonTracker AI - Phase C3 Food Carbon Engine Tests")
    print("=" * 75)

    # ──────────────────────────────────────────────────────────────────────
    # Test 1: "I ate chicken biriyani" → 1 serving × 2.50 = 2.50
    # ──────────────────────────────────────────────────────────────────────
    print("\nTest 1: 'I ate chicken biriyani' (1 serving, default)")
    r1 = calculate_food_carbon_from_text("I ate chicken biriyani")
    check("food",     r1.get("food"),     "Chicken Biriyani")
    check("servings", r1.get("servings"), 1)
    check("factor",   r1.get("factor"),   2.50)
    check("formula",  r1.get("formula"),  "1 x 2.50")
    check("co2",      r1.get("co2"),      2.50)

    # ──────────────────────────────────────────────────────────────────────
    # Test 2: "I ate 2 chicken biriyani" → 2 × 2.50 = 5.00
    # ──────────────────────────────────────────────────────────────────────
    print("\nTest 2: 'I ate 2 chicken biriyani'")
    r2 = calculate_food_carbon_from_text("I ate 2 chicken biriyani")
    check("food",     r2.get("food"),     "Chicken Biriyani")
    check("servings", r2.get("servings"), 2)
    check("formula",  r2.get("formula"),  "2 x 2.50")
    check("co2",      r2.get("co2"),      5.00)

    # ──────────────────────────────────────────────────────────────────────
    # Test 3: "I ate mutton biriyani" → 1 × 3.50 = 3.50
    # ──────────────────────────────────────────────────────────────────────
    print("\nTest 3: 'I ate mutton biriyani'")
    r3 = calculate_food_carbon_from_text("I ate mutton biriyani")
    check("food",     r3.get("food"),     "Mutton Biriyani")
    check("servings", r3.get("servings"), 1)
    check("factor",   r3.get("factor"),   3.50)
    check("co2",      r3.get("co2"),      3.50)

    # ──────────────────────────────────────────────────────────────────────
    # Test 4: "I ate sambar rice" → 1 × 0.45 = 0.45
    # ──────────────────────────────────────────────────────────────────────
    print("\nTest 4: 'I ate sambar rice'")
    r4 = calculate_food_carbon_from_text("I ate sambar rice")
    check("food",     r4.get("food"),     "Sambar Rice")
    check("servings", r4.get("servings"), 1)
    check("factor",   r4.get("factor"),   0.45)
    check("co2",      r4.get("co2"),      0.45)

    # ──────────────────────────────────────────────────────────────────────
    # Test 5: "I ate egg noodles" → 1 × 0.85 = 0.85
    # ──────────────────────────────────────────────────────────────────────
    print("\nTest 5: 'I ate egg noodles'")
    r5 = calculate_food_carbon_from_text("I ate egg noodles")
    check("food",     r5.get("food"),     "Egg Noodles")
    check("servings", r5.get("servings"), 1)
    check("factor",   r5.get("factor"),   0.85)
    check("co2",      r5.get("co2"),      0.85)

    # ──────────────────────────────────────────────────────────────────────
    # Test 6: "I ate 3 dosa" → 3 × 0.18 = 0.54
    # ──────────────────────────────────────────────────────────────────────
    print("\nTest 6: 'I ate 3 dosa'")
    r6 = calculate_food_carbon_from_text("I ate 3 dosa")
    check("food",     r6.get("food"),     "Dosa")
    check("servings", r6.get("servings"), 3)
    check("factor",   r6.get("factor"),   0.18)
    check("formula",  r6.get("formula"),  "3 x 0.18")
    check("co2",      r6.get("co2"),      0.54)

    # ──────────────────────────────────────────────────────────────────────
    # Test 7: "I ate moon burger" → unknown_food_item
    # ──────────────────────────────────────────────────────────────────────
    print("\nTest 7: 'I ate moon burger' (unknown food)")
    r7 = calculate_food_carbon_from_text("I ate moon burger")
    check("error", r7.get("error"), "unknown_food_item")

    # ──────────────────────────────────────────────────────────────────────
    # Test 8: "I ate chicken biriyani and egg noodles" → two entities
    # ──────────────────────────────────────────────────────────────────────
    print("\nTest 8: 'I ate chicken biriyani and egg noodles' (multi-entity)")
    r8 = extract_all_food_items("I ate chicken biriyani and egg noodles")
    check("count (2 items)", len(r8), 2)
    names = sorted([item.get("food", "") for item in r8])
    check("foods detected", names, sorted(["Chicken Biriyani", "Egg Noodles"]))
    # No crash / no error key
    has_error = any("error" in item for item in r8)
    check("no error in multi-result", has_error, False)

    # ──────────────────────────────────────────────────────────────────────
    # Longest Phrase Matching Verification
    # ──────────────────────────────────────────────────────────────────────
    print("\n--- Longest Phrase Matching Tests ---")

    print("\nLPM: 'I ate chicken biriyani' -> Chicken Biriyani (not just Chicken)")
    rL1 = calculate_food_carbon_from_text("I ate chicken biriyani")
    check("longest match (biriyani)", rL1.get("food"), "Chicken Biriyani")

    print("\nLPM: 'I ate mutton biriyani' -> Mutton Biriyani (not just Mutton)")
    rL2 = calculate_food_carbon_from_text("I ate mutton biriyani")
    check("longest match (mutton biriyani)", rL2.get("food"), "Mutton Biriyani")

    print("\nLPM: 'I ate egg noodles' -> Egg Noodles (not just Egg)")
    rL3 = calculate_food_carbon_from_text("I ate egg noodles")
    check("longest match (egg noodles)", rL3.get("food"), "Egg Noodles")

    print("\nLPM: 'I ate sambar rice' -> Sambar Rice (not just Rice)")
    rL4 = calculate_food_carbon_from_text("I ate sambar rice")
    check("longest match (sambar rice)", rL4.get("food"), "Sambar Rice")

    print("\nLPM: 'I ate curd rice' -> Curd Rice (not just Rice)")
    rL5 = calculate_food_carbon_from_text("I ate curd rice")
    check("longest match (curd rice)", rL5.get("food"), "Curd Rice")

    print("\nLPM: 'I ate chicken rice' -> Chicken Rice (not just Chicken)")
    rL6 = calculate_food_carbon_from_text("I ate chicken rice")
    check("longest match (chicken rice)", rL6.get("food"), "Chicken Rice")

    # ──────────────────────────────────────────────────────────────────────
    # Serving Extraction: Textual Numbers
    # ──────────────────────────────────────────────────────────────────────
    print("\n--- Serving Extraction Tests ---")

    print("\nServings: 'I had three idli' -> servings=3")
    rS1 = calculate_food_carbon_from_text("I had three idli")
    check("servings (textual three)", rS1.get("servings"), 3)

    print("\nServings: 'I ate a dosa' -> servings=1")
    rS2 = calculate_food_carbon_from_text("I ate a dosa")
    check("servings (textual a->1)", rS2.get("servings"), 1)

    print("\nServings: 'I ate dosa' -> servings=1 (default)")
    rS3 = calculate_food_carbon_from_text("I ate dosa")
    check("servings (default=1)", rS3.get("servings"), 1)

    # ──────────────────────────────────────────────────────────────────────
    # Factor Registry Completeness Check
    # ──────────────────────────────────────────────────────────────────────
    print("\n--- Factor Registry Completeness Tests ---")
    mandatory_foods = [
        "idli", "dosa", "pongal", "upma", "sambar rice", "rasam rice",
        "curd rice", "lemon rice", "tomato rice", "veg fried rice", "veg noodles",
        "coffee", "tea", "chocolate", "cake", "ice cream", "candy", "sweets",
        "egg rice", "egg noodles", "boiled egg", "omelette",
        "chicken rice", "chicken noodles", "chicken biriyani",
        "chicken burger", "chicken pizza",
        "mutton rice", "mutton biriyani",
    ]
    for food in mandatory_foods:
        f = get_food_factor(food)
        check(f"factor exists: {food}", f is not None, True)

    # ──────────────────────────────────────────────────────────────────────
    # Additional Edge Cases
    # ──────────────────────────────────────────────────────────────────────
    print("\n--- Edge Case Tests ---")

    print("\nEdge: empty input -> unknown_food_item")
    re1 = calculate_food_carbon_from_text("")
    check("empty input error", re1.get("error"), "unknown_food_item")

    print("\nEdge: 'I drove 30 km by car' -> unknown_food_item (not a food)")
    re2 = calculate_food_carbon_from_text("I drove 30 km by car")
    check("non-food input error", re2.get("error"), "unknown_food_item")

    print("\nEdge: veg fried rice (longer compound) vs plain fried rice alias")
    re3 = calculate_food_carbon_from_text("I ate veg fried rice")
    check("veg fried rice matched", re3.get("food"), "Veg Fried Rice")
    check("veg fried rice co2",     re3.get("co2"),  0.55)

    # ──────────────────────────────────────────────────────────────────────
    # Performance Benchmark
    # ──────────────────────────────────────────────────────────────────────
    print("\n=== Performance Latency Benchmark (100 runs) ===")
    t_start = time.perf_counter()
    for _ in range(100):
        calculate_food_carbon_from_text("I ate 2 chicken biriyani")
        calculate_food_carbon_from_text("I ate mutton biriyani")
        calculate_food_carbon_from_text("I ate sambar rice")
        calculate_food_carbon_from_text("I ate moon burger")
    elapsed_ms = (time.perf_counter() - t_start) * 1000.0
    avg_latency = elapsed_ms / 400.0
    print(f"  Total Benchmarked Latency : {elapsed_ms:.2f} ms")
    print(f"  Average Execution Latency : {avg_latency:.4f} ms")

    latency_ok = avg_latency < 50.0
    if latency_ok:
        PASS_COUNT += 1
        print("  [PASS] Latency requirement met (< 50 ms average)")
    else:
        FAIL_COUNT += 1
        print(f"  [FAIL] Latency too slow: {avg_latency:.4f} ms, expected < 50 ms")

    # ──────────────────────────────────────────────────────────────────────
    # Final Summary
    # ──────────────────────────────────────────────────────────────────────
    print("\n" + "=" * 75)
    total = PASS_COUNT + FAIL_COUNT
    print(f" Results: {PASS_COUNT} PASSED  |  {FAIL_COUNT} FAILED  |  {total} TOTAL")
    print("=" * 75)

    if FAIL_COUNT > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    run_tests()
