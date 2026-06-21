"""
waste_tests.py
==============
CarbonTracker AI - Phase C4 Waste Carbon Engine Verification Tests

Test Matrix (per specification):
    Test 1: "I disposed 2 kg plastic waste"          -> 12.00 kg CO2
    Test 2: "I recycled 1 kg e-waste"                -> 12.00 kg CO2
    Test 3: "I disposed 3 kg organic waste"          -> 1.50 kg CO2
    Test 4: "I disposed 500 g paper waste"           -> 0.65 kg CO2
    Test 5: "I disposed 2 kg battery waste"          -> 30.00 kg CO2
    Test 6: "I disposed moon dust"                   -> unknown_waste_type
    Test 7: "1 kg plastic waste and 2 kg paper waste"-> Multi-entity detection

Plus:
    - Alias resolution (electronic waste, kitchen waste, etc.)
    - Gram-to-kg conversion accuracy
    - Longest-phrase matching
    - Factor registry completeness
    - Edge cases
    - Performance benchmark
"""

import sys
import os
import time

# Ensure backend root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.carbon.waste_carbon_engine import (
    calculate_waste_carbon_from_text,
    extract_all_waste_items,
)
from app.carbon.waste_factors import WASTE_FACTORS, get_waste_factor
from app.carbon.waste_formula import grams_to_kg, calculate_waste_carbon, format_waste_formula

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
    """Floating-point approximate comparison."""
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
    print(" CarbonTracker AI - Phase C4 Waste Carbon Engine Tests")
    print("=" * 75)

    # -------------------------------------------------------------------------
    # Test 1: "I disposed 2 kg plastic waste" -> 2 x 6.0 = 12.00
    # -------------------------------------------------------------------------
    print("\nTest 1: 'I disposed 2 kg plastic waste'")
    r1 = calculate_waste_carbon_from_text("I disposed 2 kg plastic waste")
    check("waste_type", r1.get("waste_type"), "Plastic Waste")
    check("weight",     r1.get("weight"),     2.0)
    check("factor",     r1.get("factor"),     6.0)
    check("formula",    r1.get("formula"),    "2 x 6.0")
    check("carbon",     r1.get("carbon"),     12.0)

    # -------------------------------------------------------------------------
    # Test 2: "I recycled 1 kg e-waste" -> 1 x 12.0 = 12.00
    # -------------------------------------------------------------------------
    print("\nTest 2: 'I recycled 1 kg e-waste'")
    r2 = calculate_waste_carbon_from_text("I recycled 1 kg e-waste")
    check("waste_type", r2.get("waste_type"), "E-Waste")
    check("weight",     r2.get("weight"),     1.0)
    check("factor",     r2.get("factor"),     12.0)
    check("formula",    r2.get("formula"),    "1 x 12.0")
    check("carbon",     r2.get("carbon"),     12.0)

    # -------------------------------------------------------------------------
    # Test 3: "I disposed 3 kg organic waste" -> 3 x 0.5 = 1.50
    # -------------------------------------------------------------------------
    print("\nTest 3: 'I disposed 3 kg organic waste'")
    r3 = calculate_waste_carbon_from_text("I disposed 3 kg organic waste")
    check("waste_type", r3.get("waste_type"), "Organic Waste")
    check("weight",     r3.get("weight"),     3.0)
    check("factor",     r3.get("factor"),     0.5)
    check("carbon",     r3.get("carbon"),     1.5)

    # -------------------------------------------------------------------------
    # Test 4: "I disposed 500 g paper waste" -> 0.5 x 1.3 = 0.65
    # -------------------------------------------------------------------------
    print("\nTest 4: 'I disposed 500 g paper waste'")
    r4 = calculate_waste_carbon_from_text("I disposed 500 g paper waste")
    check("waste_type", r4.get("waste_type"), "Paper Waste")
    check("weight",     r4.get("weight"),     0.5)
    check("factor",     r4.get("factor"),     1.3)
    check("carbon",     r4.get("carbon"),     0.65)

    # -------------------------------------------------------------------------
    # Test 5: "I disposed 2 kg battery waste" -> 2 x 15.0 = 30.00
    # -------------------------------------------------------------------------
    print("\nTest 5: 'I disposed 2 kg battery waste'")
    r5 = calculate_waste_carbon_from_text("I disposed 2 kg battery waste")
    check("waste_type", r5.get("waste_type"), "Battery Waste")
    check("weight",     r5.get("weight"),     2.0)
    check("factor",     r5.get("factor"),     15.0)
    check("formula",    r5.get("formula"),    "2 x 15.0")
    check("carbon",     r5.get("carbon"),     30.0)

    # -------------------------------------------------------------------------
    # Test 6: "I disposed moon dust" -> unknown_waste_type
    # -------------------------------------------------------------------------
    print("\nTest 6: 'I disposed moon dust' (unknown waste)")
    r6 = calculate_waste_carbon_from_text("I disposed moon dust")
    check("error", r6.get("error"), "unknown_waste_type")

    # -------------------------------------------------------------------------
    # Test 7: Multi-entity detection
    # -------------------------------------------------------------------------
    print("\nTest 7: '1 kg plastic waste and 2 kg paper waste' (multi-entity)")
    r7 = extract_all_waste_items("I disposed 1 kg plastic waste and 2 kg paper waste")
    check("count (2 items)", len(r7), 2)
    types = sorted([item.get("waste_type", "") for item in r7])
    check("waste types", types, sorted(["Plastic Waste", "Paper Waste"]))
    has_error = any("error" in item for item in r7)
    check("no error in multi-result", has_error, False)

    # -------------------------------------------------------------------------
    # Unit Conversion Tests
    # -------------------------------------------------------------------------
    print("\n--- Unit Conversion Tests ---")

    print("\nConversion: 500 g -> 0.5 kg")
    check("grams_to_kg(500)", grams_to_kg(500), 0.5)

    print("\nConversion: 1000 g -> 1.0 kg")
    check("grams_to_kg(1000)", grams_to_kg(1000), 1.0)

    print("\nConversion: 250 g -> 0.25 kg")
    check("grams_to_kg(250)", grams_to_kg(250), 0.25)

    print("\n500 g glass waste -> 0.5 x 0.9 = 0.45")
    rU1 = calculate_waste_carbon_from_text("I disposed 500 g glass waste")
    check("waste_type", rU1.get("waste_type"), "Glass Waste")
    check("weight",     rU1.get("weight"),     0.5)
    check("carbon",     rU1.get("carbon"),     0.45)

    print("\n250 g metal waste -> 0.25 x 2.1 = 0.53")
    rU2 = calculate_waste_carbon_from_text("I disposed 250 g metal waste")
    check("waste_type", rU2.get("waste_type"), "Metal Waste")
    check_close("weight", rU2.get("weight"), 0.25)
    check("carbon",     rU2.get("carbon"),     0.53)

    # -------------------------------------------------------------------------
    # Alias Resolution Tests
    # -------------------------------------------------------------------------
    print("\n--- Alias Resolution Tests ---")

    print("\nAlias: 'electronic waste' -> E-Waste")
    rA1 = calculate_waste_carbon_from_text("I disposed 1 kg electronic waste")
    check("waste_type (electronic waste)", rA1.get("waste_type"), "E-Waste")
    check("factor", rA1.get("factor"), 12.0)

    print("\nAlias: 'mobile waste' -> E-Waste")
    rA2 = calculate_waste_carbon_from_text("I disposed 1 kg mobile waste")
    check("waste_type (mobile waste)", rA2.get("waste_type"), "E-Waste")

    print("\nAlias: 'kitchen waste' -> Organic Waste")
    rA3 = calculate_waste_carbon_from_text("I disposed 2 kg kitchen waste")
    check("waste_type (kitchen waste)", rA3.get("waste_type"), "Organic Waste")
    check("factor", rA3.get("factor"), 0.5)

    print("\nAlias: 'vegetable waste' -> Organic Waste")
    rA4 = calculate_waste_carbon_from_text("I disposed 1 kg vegetable waste")
    check("waste_type (vegetable waste)", rA4.get("waste_type"), "Organic Waste")

    print("\nAlias: 'laptop waste' -> E-Waste")
    rA5 = calculate_waste_carbon_from_text("I disposed 2 kg laptop waste")
    check("waste_type (laptop waste)", rA5.get("waste_type"), "E-Waste")

    # -------------------------------------------------------------------------
    # Longest Phrase Matching Tests
    # -------------------------------------------------------------------------
    print("\n--- Longest Phrase Matching Tests ---")

    print("\nLPM: 'plastic waste' -> Plastic Waste (not just 'plastic')")
    rL1 = calculate_waste_carbon_from_text("I disposed 1 kg plastic waste")
    check("longest match (plastic waste)", rL1.get("waste_type"), "Plastic Waste")

    print("\nLPM: 'battery waste' -> Battery Waste (not just 'battery')")
    rL2 = calculate_waste_carbon_from_text("I disposed 1 kg battery waste")
    check("longest match (battery waste)", rL2.get("waste_type"), "Battery Waste")

    print("\nLPM: 'food waste' -> Food Waste (not organic waste)")
    rL3 = calculate_waste_carbon_from_text("I disposed 1 kg food waste")
    check("longest match (food waste)", rL3.get("waste_type"), "Food Waste")
    check("factor (food waste = 0.8)", rL3.get("factor"), 0.8)

    # -------------------------------------------------------------------------
    # Factor Registry Completeness
    # -------------------------------------------------------------------------
    print("\n--- Factor Registry Completeness Tests ---")
    mandatory = [
        ("plastic waste", 6.0),
        ("e-waste",       12.0),
        ("battery waste", 15.0),
        ("organic waste", 0.5),
        ("food waste",    0.8),
        ("paper waste",   1.3),
        ("glass waste",   0.9),
        ("metal waste",   2.1),
    ]
    for waste_key, expected_factor in mandatory:
        f = get_waste_factor(waste_key)
        check(f"factor exists: {waste_key}", f, expected_factor)

    # -------------------------------------------------------------------------
    # Formula String Tests
    # -------------------------------------------------------------------------
    print("\n--- Formula String Tests ---")
    check("format_waste_formula(2, 6.0)",   format_waste_formula(2, 6.0),   "2 x 6.0")
    check("format_waste_formula(0.5, 1.3)", format_waste_formula(0.5, 1.3), "0.5 x 1.3")
    check("format_waste_formula(1, 12.0)",  format_waste_formula(1, 12.0),  "1 x 12.0")
    check("format_waste_formula(3, 0.5)",   format_waste_formula(3, 0.5),   "3 x 0.5")

    # -------------------------------------------------------------------------
    # Edge Cases
    # -------------------------------------------------------------------------
    print("\n--- Edge Case Tests ---")

    print("\nEdge: empty input -> unknown_waste_type")
    rE1 = calculate_waste_carbon_from_text("")
    check("empty input error", rE1.get("error"), "unknown_waste_type")

    print("\nEdge: non-waste input -> unknown_waste_type")
    rE2 = calculate_waste_carbon_from_text("I drove 30 km by car")
    check("non-waste input error", rE2.get("error"), "unknown_waste_type")

    print("\nEdge: known waste but no weight -> weight_required")
    rE3 = calculate_waste_carbon_from_text("I disposed plastic waste")
    check("weight_required error", rE3.get("error"), "weight_required")

    print("\nEdge: 1000 g -> 1 kg plastic waste -> 6.0")
    rE4 = calculate_waste_carbon_from_text("I disposed 1000 g plastic waste")
    check("1000g -> 1kg plastic carbon", rE4.get("carbon"), 6.0)

    # -------------------------------------------------------------------------
    # Direct Formula Calculation Tests
    # -------------------------------------------------------------------------
    print("\n--- Direct Formula Calculation Tests ---")
    check("2 x 6.0 = 12.0",  calculate_waste_carbon(2.0, 6.0),  12.0)
    check("1 x 12.0 = 12.0", calculate_waste_carbon(1.0, 12.0), 12.0)
    check("3 x 0.5 = 1.5",   calculate_waste_carbon(3.0, 0.5),  1.5)
    check("5 x 1.3 = 6.5",   calculate_waste_carbon(5.0, 1.3),  6.5)
    check("0.5 x 0.9 = 0.45",calculate_waste_carbon(0.5, 0.9),  0.45)
    check("2 x 15.0 = 30.0", calculate_waste_carbon(2.0, 15.0), 30.0)
    check("2 x 2.1 = 4.2",   calculate_waste_carbon(2.0, 2.1),  4.2)

    # -------------------------------------------------------------------------
    # Performance Benchmark
    # -------------------------------------------------------------------------
    print("\n=== Performance Latency Benchmark (100 runs) ===")
    t_start = time.perf_counter()
    for _ in range(100):
        calculate_waste_carbon_from_text("I disposed 2 kg plastic waste")
        calculate_waste_carbon_from_text("I recycled 1 kg e-waste")
        calculate_waste_carbon_from_text("I disposed 500 g paper waste")
        calculate_waste_carbon_from_text("I disposed moon dust")
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

    # -------------------------------------------------------------------------
    # Final Summary
    # -------------------------------------------------------------------------
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
