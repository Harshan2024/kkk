import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.carbon.energy_carbon_engine import calculate_energy_carbon

PASS_COUNT = 0
FAIL_COUNT = 0


def check(label, actual, expected):
    global PASS_COUNT, FAIL_COUNT
    ok = (actual == expected)
    status = "PASS" if ok else "FAIL"
    if ok:
        PASS_COUNT += 1
        print("  [%s] %s: %r" % (status, label, actual))
    else:
        FAIL_COUNT += 1
        print("  [%s] %s: got %r, expected %r" % (status, label, actual, expected))
    return ok


def run_tests():
    global PASS_COUNT, FAIL_COUNT

    print("=" * 75)
    print(" CarbonTracker AI - Phase C2 Energy Carbon Engine Tests")
    print("=" * 75)

    # ------------------------------------------------------------------
    # Test 1: 135W charger, 90 mins
    # kW=0.135 | hours=1.5 | kWh=0.2025 | CO2=0.2025*0.82=0.16605 -> 0.17
    # ------------------------------------------------------------------
    print("\nTest 1: 135W Charger, 90 minutes")
    r1 = calculate_energy_carbon("Laptop Charger", power=135, duration=90, duration_unit="minutes")
    check("co2",           r1.get("co2"),           0.17)
    check("power_watts",   r1.get("power_watts"),   135.0)
    check("duration_hours",r1.get("duration_hours"),1.5)
    check("energy_kwh",    round(r1.get("energy_kwh", 0), 4), 0.2025)
    check("formula",       r1.get("formula"),       "0.2025 x 0.82")

    # ------------------------------------------------------------------
    # Test 2: 60W charger, 1 hour
    # kW=0.06 | kWh=0.06 | CO2=0.06*0.82=0.0492 -> 0.05
    # ------------------------------------------------------------------
    print("\nTest 2: 60W Charger, 1 hour")
    r2 = calculate_energy_carbon("Charger", power=60, duration=1, duration_unit="hours")
    check("co2",           r2.get("co2"),           0.05)
    check("power_watts",   r2.get("power_watts"),   60.0)
    check("energy_kwh",    round(r2.get("energy_kwh", 0), 4), 0.06)
    check("formula",       r2.get("formula"),       "0.06 x 0.82")

    # ------------------------------------------------------------------
    # Test 3: AC 1500W, 3 hours
    # kW=1.5 | kWh=4.5 | CO2=4.5*0.82=3.69
    # ------------------------------------------------------------------
    print("\nTest 3: AC (1500W), 3 hours")
    r3 = calculate_energy_carbon("AC", power=1500, duration=3, duration_unit="hours")
    check("co2",           r3.get("co2"),           3.69)
    check("energy_kwh",    round(r3.get("energy_kwh", 0), 4), 4.5)
    check("formula",       r3.get("formula"),       "4.5 x 0.82")

    # ------------------------------------------------------------------
    # Test 4: Fan 75W, 8 hours
    # kW=0.075 | kWh=0.6 | CO2=0.6*0.82=0.492 -> 0.49
    # ------------------------------------------------------------------
    print("\nTest 4: Fan (75W), 8 hours")
    r4 = calculate_energy_carbon("Fan", power=75, duration=8, duration_unit="hours")
    check("co2",           r4.get("co2"),           0.49)
    check("energy_kwh",    round(r4.get("energy_kwh", 0), 4), 0.6)
    check("formula",       r4.get("formula"),       "0.6 x 0.82")

    # ------------------------------------------------------------------
    # Test 5: Refrigerator 150W, 24 hours
    # kW=0.15 | kWh=3.6 | CO2=3.6*0.82=2.952 -> 2.95
    # ------------------------------------------------------------------
    print("\nTest 5: Refrigerator (150W), 24 hours")
    r5 = calculate_energy_carbon("Refrigerator", power=150, duration=24, duration_unit="hours")
    check("co2",           r5.get("co2"),           2.95)
    check("energy_kwh",    round(r5.get("energy_kwh", 0), 4), 3.6)
    check("formula",       r5.get("formula"),       "3.6 x 0.82")

    # ------------------------------------------------------------------
    # Test 6: Mobile Charger 20W, 2 hours
    # kW=0.02 | kWh=0.04 | CO2=0.04*0.82=0.0328 -> 0.03
    # ------------------------------------------------------------------
    print("\nTest 6: Mobile Charger (20W), 2 hours")
    r6 = calculate_energy_carbon("Mobile Charger", power=20, duration=2, duration_unit="hours")
    check("co2",           r6.get("co2"),           0.03)
    check("energy_kwh",    round(r6.get("energy_kwh", 0), 4), 0.04)
    check("formula",       r6.get("formula"),       "0.04 x 0.82")

    # ------------------------------------------------------------------
    # Test 7: 0W -> invalid_power
    # ------------------------------------------------------------------
    print("\nTest 7: 0W (invalid power)")
    r7 = calculate_energy_carbon("Laptop", power=0, duration=1, duration_unit="hours")
    check("error",         r7.get("error"),         "invalid_power")

    # ------------------------------------------------------------------
    # Test 8: -2 hours -> invalid_duration
    # ------------------------------------------------------------------
    print("\nTest 8: -2 hours (invalid duration)")
    r8 = calculate_energy_carbon("Laptop", power=65, duration=-2, duration_unit="hours")
    check("error",         r8.get("error"),         "invalid_duration")

    # ------------------------------------------------------------------
    # Test 9: 99999W -> invalid_power (exceeds MAX_POWER_WATTS=10000)
    # ------------------------------------------------------------------
    print("\nTest 9: 99999W (exceeds max power limit)")
    r9 = calculate_energy_carbon("Unknown", power=99999, duration=1, duration_unit="hours")
    check("error",         r9.get("error"),         "invalid_power")

    # ------------------------------------------------------------------
    # Power Priority Tests
    # ------------------------------------------------------------------
    print("\n--- Power Priority Tests ---")

    print("\nPriority Rule 1: User power (2000W) overrides AC catalog (1500W)")
    rp1 = calculate_energy_carbon("AC", power=2000, duration=1, duration_unit="hours")
    check("power_watts (user override)",    rp1.get("power_watts"), 2000.0)

    print("\nPriority Rule 2: Catalog fallback for AC (no power supplied)")
    rp2 = calculate_energy_carbon("AC", power=None, duration=1, duration_unit="hours")
    check("power_watts (catalog fallback)", rp2.get("power_watts"), 1500.0)

    # ------------------------------------------------------------------
    # Duration Edge Tests
    # ------------------------------------------------------------------
    print("\n--- Duration Edge Tests ---")

    print("\nEdge: 0 minutes -> invalid_duration")
    re1 = calculate_energy_carbon("Fan", power=75, duration=0, duration_unit="minutes")
    check("error", re1.get("error"), "invalid_duration")

    print("\nEdge: 169 hours -> invalid_duration (exceeds 1 week)")
    re2 = calculate_energy_carbon("Fridge", power=150, duration=169, duration_unit="hours")
    check("error", re2.get("error"), "invalid_duration")

    # ------------------------------------------------------------------
    # Minutes Conversion Test
    # ------------------------------------------------------------------
    print("\n--- Minutes to Hours Conversion Test ---")
    print("\nConversion: 90 min = 1.5 hours")
    rc = calculate_energy_carbon("Laptop", power=65, duration=90, duration_unit="minutes")
    check("duration_hours", rc.get("duration_hours"), 1.5)

    # ------------------------------------------------------------------
    # Unknown Device Test
    # ------------------------------------------------------------------
    print("\n--- Unknown Device Test ---")
    print("\nUnknown device without power supplied")
    ru = calculate_energy_carbon("Toaster", power=None, duration=1, duration_unit="hours")
    check("error", ru.get("error"), "unknown_device")

    # ------------------------------------------------------------------
    # Performance Benchmark
    # ------------------------------------------------------------------
    print("\n=== Performance Latency Benchmarking (100 runs) ===")
    t_start = time.perf_counter()
    for _ in range(100):
        calculate_energy_carbon("AC", power=1500, duration=3, duration_unit="hours")
        calculate_energy_carbon("Laptop Charger", power=135, duration=90, duration_unit="minutes")
    elapsed_ms = (time.perf_counter() - t_start) * 1000.0
    avg_latency = elapsed_ms / 200.0
    print("  Total Benchmarked Latency: %.2f ms" % elapsed_ms)
    print("  Average Execution Latency: %.4f ms" % avg_latency)

    latency_ok = avg_latency < 20.0
    if latency_ok:
        PASS_COUNT += 1
        print("  [PASS] Latency requirement met (< 20ms average)")
    else:
        FAIL_COUNT += 1
        print("  [FAIL] Latency too slow: %.4f ms, expected < 20.0 ms" % avg_latency)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 75)
    total = PASS_COUNT + FAIL_COUNT
    print(" Results: %d PASSED  |  %d FAILED  |  %d TOTAL" % (PASS_COUNT, FAIL_COUNT, total))
    print("=" * 75)

    if FAIL_COUNT > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    run_tests()
