import sys
import os
import time

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/../../"))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.carbon.transport_carbon_engine import calculate_transport_from_text

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

def run_tests():
    global PASS_COUNT, FAIL_COUNT
    print("=" * 75)
    print(" CarbonTracker AI — Phase C1 Transport Carbon Engine Tests")
    print("=" * 75)

    # Test 1: 'I ran 5 km'
    print("\nTest 1: 'I ran 5 km'")
    res1 = calculate_transport_from_text("I ran 5 km")
    check("co2", res1.get("co2"), 0.0)
    check("formula", res1.get("formula"), "5 × 0.000")

    # Test 2: 'I cycled 10 km'
    print("\nTest 2: 'I cycled 10 km'")
    res2 = calculate_transport_from_text("I cycled 10 km")
    check("co2", res2.get("co2"), 0.0)
    check("formula", res2.get("formula"), "10 × 0.000")

    # Test 3: 'I drove 20 km'
    print("\nTest 3: 'I drove 20 km'")
    res3 = calculate_transport_from_text("I drove 20 km")
    check("co2", res3.get("co2"), 3.84)
    check("formula", res3.get("formula"), "20 × 0.192")

    # Test 4: 'I travelled 50 km by bus'
    print("\nTest 4: 'I travelled 50 km by bus'")
    res4 = calculate_transport_from_text("I travelled 50 km by bus")
    check("co2", res4.get("co2"), 5.25)
    check("formula", res4.get("formula"), "50 × 0.105")

    # Test 5: 'I travelled from Chennai to Madurai by electric train'
    print("\nTest 5: 'I travelled from Chennai to Madurai by electric train'")
    res5 = calculate_transport_from_text("I travelled from Chennai to Madurai by electric train")
    check("co2", res5.get("co2"), 9.24)
    check("formula", res5.get("formula"), "462 × 0.020")

    # Test 6: 'I flew from Chennai to Delhi'
    print("\nTest 6: 'I flew from Chennai to Delhi'")
    res6 = calculate_transport_from_text("I flew from Chennai to Delhi")
    check("co2", res6.get("co2"), 448.80)
    check("formula", res6.get("formula"), "1760 × 0.255")

    # Test 7: 'I travelled 15 km by electric scooter'
    print("\nTest 7: 'I travelled 15 km by electric scooter'")
    res7 = calculate_transport_from_text("I travelled 15 km by electric scooter")
    check("co2", res7.get("co2"), 0.23)
    check("formula", res7.get("formula"), "15 × 0.015")

    # Test 8: Unknown Vehicle
    print("\nTest 8: Unknown vehicle - 'I rode a spaceship 10 km'")
    res8 = calculate_transport_from_text("I rode a spaceship 10 km")
    check("error", res8.get("error"), "unknown_transport_mode")

    # Distance Policy: Missing Distance Test
    print("\nTest: Missing distance - 'I commuted by car'")
    res_miss = calculate_transport_from_text("I commuted by car")
    check("error", res_miss.get("error"), "distance_required")
    check("message", res_miss.get("message"), "Please specify the travel distance in kilometers.")

    # Context-Aware Two-Wheeler Ambiguity Tests
    print("\nTest 9: 'I travelled 5 km in a petrol bike.'")
    res9 = calculate_transport_from_text("I travelled 5 km in a petrol bike.")
    check("vehicle", res9.get("vehicle"), "Petrol Motorcycle")
    check("Vehicle Type", res9.get("Vehicle Type"), "Petrol Motorcycle")
    check("Fuel Type", res9.get("Fuel Type"), "Petrol")
    check("co2", res9.get("co2"), 0.52)
    check("formula", res9.get("formula"), "5 × 0.103")

    print("\nTest 10: 'I rode my bike with a helmet for 10 km'")
    res10 = calculate_transport_from_text("I rode my bike with a helmet for 10 km")
    check("vehicle", res10.get("vehicle"), "Motorcycle")
    check("Vehicle Type", res10.get("Vehicle Type"), "Motorcycle")
    check("Fuel Type", res10.get("Fuel Type"), "Petrol")
    check("co2", res10.get("co2"), 1.03)

    print("\nTest 11: 'I rode my bike with pedals for 12 km'")
    res11 = calculate_transport_from_text("I rode my bike with pedals for 12 km")
    check("vehicle", res11.get("vehicle"), "Bicycle")
    check("Vehicle Type", res11.get("Vehicle Type"), "Bicycle")
    check("Fuel Type", res11.get("Fuel Type"), "None")
    check("co2", res11.get("co2"), 0.0)

    print("\nTest 12: 'I rode a honda for 15 km'")
    res12 = calculate_transport_from_text("I rode a honda for 15 km")
    check("vehicle", res12.get("vehicle"), "Motorcycle")
    check("Vehicle Type", res12.get("Vehicle Type"), "Motorcycle")
    check("Fuel Type", res12.get("Fuel Type"), "Petrol")
    check("co2", res12.get("co2"), 1.55)

    print("\nTest 13: 'I rode an electric bike for 6 km'")
    res13 = calculate_transport_from_text("I rode an electric bike for 6 km")
    check("vehicle", res13.get("vehicle"), "Electric Bike")
    check("Vehicle Type", res13.get("Vehicle Type"), "Electric Bike")
    check("Fuel Type", res13.get("Fuel Type"), "Electric")
    check("co2", res13.get("co2"), 0.12)

    print("\nTest 14: 'I rode my bike with engine for 20 km'")
    res14 = calculate_transport_from_text("I rode my bike with engine for 20 km")
    check("vehicle", res14.get("vehicle"), "Motorcycle")

    print("\nTest 15: 'I rode my bike riding for 25 km'")
    res15 = calculate_transport_from_text("I rode my bike riding for 25 km")
    check("vehicle", res15.get("vehicle"), "Motorcycle")

    print("\nTest 16: 'I rode my bike to go cycling 4 km'")
    res16 = calculate_transport_from_text("I rode my bike to go cycling 4 km")
    check("vehicle", res16.get("vehicle"), "Bicycle")

    print("\nTest 17: 'I rode my bike on fuel for 30 km'")
    res17 = calculate_transport_from_text("I rode my bike on fuel for 30 km")
    check("vehicle", res17.get("vehicle"), "Petrol Motorcycle")

    # Performance & Latency Check
    print("\n=== Performance Latency Benchmarking (100 runs) ===")
    t_start = time.perf_counter()
    for _ in range(100):
        calculate_transport_from_text("I drove 20 km")
        calculate_transport_from_text("I travelled from Chennai to Madurai by electric train")
    elapsed_total_ms = (time.perf_counter() - t_start) * 1000.0
    avg_latency = elapsed_total_ms / 200.0
    print(f"  Total Benchmarked Latency: {elapsed_total_ms:.2f} ms")
    print(f"  Average Execution Latency: {avg_latency:.4f} ms")
    
    # Assert performance threshold (< 20ms average)
    latency_ok = avg_latency < 20.0
    status = "PASS" if latency_ok else "FAIL"
    if latency_ok:
        PASS_COUNT += 1
        print(f"  [{status}] Latency requirement met (< 20ms average)")
    else:
        FAIL_COUNT += 1
        print(f"  [{status}] Latency too slow: got {avg_latency:.4f} ms, expected < 20.0 ms")

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
