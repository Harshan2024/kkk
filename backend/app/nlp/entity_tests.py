import sys
import os

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/../../"))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.nlp.entity_engine import extract_entities, extract_multi_entities

PASS_COUNT = 0
FAIL_COUNT = 0

def check(label: str, actual, expected) -> bool:
    global PASS_COUNT, FAIL_COUNT
    ok = (str(actual).lower() == str(expected).lower()) if actual is not None else False
    status = "PASS" if ok else "FAIL"
    if ok:
        PASS_COUNT += 1
        print(f"  [{status}] {label}: {actual!r}")
    else:
        FAIL_COUNT += 1
        print(f"  [{status}] {label}: got {actual!r}, expected {expected!r}")
    return ok

def run_tests():
    print("=" * 70)
    print(" CarbonTracker AI — Phase B Entity Recognition Engine Tests")
    print("=" * 70)

    # Test 1
    print("\nTest 1: 'I did yoga for 1 hour'")
    res1 = extract_entities("I did yoga for 1 hour")
    check("activity", res1.get("activity"), "Yoga")
    check("duration", res1.get("duration"), 1)
    
    # Test 2
    print("\nTest 2: 'I ran 5 km'")
    res2 = extract_entities("I ran 5 km")
    check("activity", res2.get("activity"), "Running")
    check("distance", res2.get("distance"), 5)

    # Test 3
    print("\nTest 3: 'I ate chicken biriyani'")
    res3 = extract_entities("I ate chicken biriyani")
    check("food", res3.get("food"), "Chicken Biriyani")

    # Test 4
    print("\nTest 4: 'I travelled from Chennai to Madurai by electric train'")
    res4 = extract_entities("I travelled from Chennai to Madurai by electric train")
    check("source", res4.get("source"), "Chennai")
    check("destination", res4.get("destination"), "Madurai")
    check("vehicle", res4.get("vehicle"), "Electric Train")

    # Test 5
    print("\nTest 5: 'I bought a laptop'")
    res5 = extract_entities("I bought a laptop")
    check("product", res5.get("product"), "Laptop")

    # Test 6
    print("\nTest 6: 'I used AC for 3 hours'")
    res6 = extract_entities("I used AC for 3 hours")
    check("device", res6.get("device"), "AC")
    check("duration", res6.get("duration"), 3)

    # Test 7
    print("\nTest 7: 'I disposed 2 kg plastic waste'")
    res7 = extract_entities("I disposed 2 kg plastic waste")
    check("waste_type", res7.get("waste_type"), "Plastic Waste")
    check("weight", res7.get("weight"), 2)

    # Test 8
    print("\nTest 8: 'I ate chiken briyani'")
    res8 = extract_entities("I ate chiken briyani")
    check("food", res8.get("food"), "Chicken Biriyani")
    check("matched_by", res8.get("matched_by"), "synonym")

    # Unknown Handling Test
    print("\nTest: Unknown handling - 'Yoga' (as random shopping/food word)")
    res_un = extract_entities("Yoga", intent="food")
    check("food (unknown context)", res_un.get("entity"), "unknown")
    check("confidence", res_un.get("confidence"), 0.0)

    print("\nTest: Unknown handling - 'xyz abc random text'")
    res_rand = extract_entities("xyz abc random text")
    check("entity", res_rand.get("entity"), "unknown")
    check("confidence", res_rand.get("confidence"), 0.0)
    check("matched_by", res_rand.get("matched_by"), "none")

    # Multi-Entity Support Test
    print("\nTest: Multi-Entity Support - 'I travelled by train and ate biriyani'")
    multi_res = extract_multi_entities("I travelled by train and ate biriyani")
    check("multi_res length", len(multi_res), 2)
    if len(multi_res) >= 2:
        check("multi_res[0] intent", multi_res[0].get("intent"), "transport")
        check("multi_res[0] vehicle", multi_res[0].get("vehicle"), "Train")
        check("multi_res[1] intent", multi_res[1].get("intent"), "food")
        check("multi_res[1] food", multi_res[1].get("food"), "Biriyani")

    print("\n" + "=" * 70)
    total = PASS_COUNT + FAIL_COUNT
    print(f" Results: {PASS_COUNT} PASSED  |  {FAIL_COUNT} FAILED  |  {total} TOTAL")
    print("=" * 70)

    if FAIL_COUNT > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    run_tests()
