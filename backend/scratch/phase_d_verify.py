import urllib.request
import json
import urllib.parse
import time
import sys

BASE_URL = "http://127.0.0.1:8001/api/v1"

def test_parse(text):
    url = f"{BASE_URL}/activities/parse?text={urllib.parse.quote(text)}&region=Global"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"HTTP {e.code} Error for text '{text}': {body}")
        try:
            return json.loads(body)
        except:
            return {"status": "error", "error": body}
    except Exception as e:
        print(f"Connection error: {e}")
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    print("=" * 70)
    print(" PHASE D SPRINT VERIFICATION START")
    print("=" * 70)
    
    # Wait for server to spin up
    time.sleep(2)

    # 1. Transport + Food
    print("\nCase 1: Transport + Food")
    r = test_parse("I drove 10 km and ate chicken biriyani")
    assert r.get("status") == "success", f"Failed: {r}"
    assert len(r["entities"]) == 2, f"Expected 2 entities, got {len(r['entities'])}"
    assert r["entities"][0]["entity"] == "Petrol Car"
    assert r["entities"][1]["entity"] == "Chicken Biriyani"
    assert r["total_carbon"] == round(10 * 0.192 + 2.50, 4)
    print("  -> PASS")

    # 2. Transport + Energy
    print("\nCase 2: Transport + Energy")
    r = test_parse("I rode 5 km in metro and used AC for 2 hours")
    assert r.get("status") == "success"
    assert len(r["entities"]) == 2
    assert r["entities"][0]["entity"] == "Metro"
    assert r["entities"][1]["entity"] == "Air Conditioner"
    print("  -> PASS")

    # 3. Transport + Waste
    print("\nCase 3: Transport + Waste")
    r = test_parse("I rode electric train 25 km and recycled 1 kg electronic waste")
    assert r.get("status") == "success"
    assert len(r["entities"]) == 2
    assert r["entities"][0]["entity"] == "Electric Train"
    assert r["entities"][1]["entity"] == "E-Waste"
    assert r["total_carbon"] == round(25 * 0.020 + 12.00, 4)
    print("  -> PASS")

    # 4. Food + Waste
    print("\nCase 4: Food + Waste")
    r = test_parse("I ate egg noodles and disposed 2 kg plastic waste")
    assert r.get("status") == "success"
    assert len(r["entities"]) == 2
    assert r["entities"][0]["entity"] == "Egg Noodles"
    assert r["entities"][1]["entity"] == "Plastic Waste"
    assert r["total_carbon"] == round(0.85 + 2 * 6.0, 4)
    print("  -> PASS")

    # 5. Food + Energy
    print("\nCase 5: Food + Energy")
    r = test_parse("I ate dosa and used fan for 3 hours")
    assert r.get("status") == "success"
    assert len(r["entities"]) == 2
    assert r["entities"][0]["entity"] == "Dosa"
    assert r["entities"][1]["entity"] == "Fan"
    print("  -> PASS")

    # 6. Transport + Food + Energy + Waste
    print("\nCase 6: Transport + Food + Energy + Waste")
    r = test_parse("I travelled 25 km by electric train, ate 2 chicken biriyani, used AC for 3 hours and disposed 2 kg plastic waste")
    assert r.get("status") == "success"
    assert len(r["entities"]) == 4
    assert r["entities"][0]["entity"] == "Electric Train"
    assert r["entities"][1]["entity"] == "Chicken Biriyani"
    assert r["entities"][2]["entity"] == "Air Conditioner"
    assert r["entities"][3]["entity"] == "Plastic Waste"
    print("  -> PASS")

    # 7. Unknown mixed with valid
    print("\nCase 7: Unknown mixed with valid")
    r = test_parse("I ate chicken biriyani and spaceship")
    assert r.get("status") == "success"
    assert len(r["entities"]) == 2
    assert r["entities"][0]["entity"] == "Chicken Biriyani"
    assert r["entities"][1]["entity"] == "Unknown Entity"
    assert r["entities"][1]["quantity"] == 0.0
    assert r["entities"][1]["subtotal"] == 0.0
    assert r["total_carbon"] == 2.50
    print("  -> PASS")

    r = test_parse("I recycled 1 kg plastic waste and unknown material")
    assert r.get("status") == "success"
    assert len(r["entities"]) == 2
    assert r["entities"][0]["entity"] == "Plastic Waste"
    assert r["entities"][1]["entity"] == "Unknown Entity"
    assert r["entities"][1]["subtotal"] == 0.0
    assert r["total_carbon"] == 6.0
    print("  -> PASS")

    # 8. Large multi-entity inputs
    print("\nCase 8: Large multi-entity inputs")
    r = test_parse("I ate 2 chicken biriyani, 1 egg noodles, used fan for 3 hours, drove 10 km and disposed 1 kg e-waste")
    assert r.get("status") == "success"
    assert len(r["entities"]) == 5
    print("  -> PASS")

    # 9. Duplicate handling
    print("\nCase 9: Duplicate handling")
    r = test_parse("I ate chicken biriyani and chicken biriyani")
    assert r.get("status") == "success"
    assert len(r["entities"]) == 2
    assert r["entities"][0]["entity"] == "Chicken Biriyani"
    assert r["entities"][1]["entity"] == "Chicken Biriyani"
    assert r["total_carbon"] == 5.0
    print("  -> PASS")

    print("\n" + "=" * 70)
    print(" ALL PHASE D VERIFICATION CASES PASSED SUCCESSFULLY!")
    print("=" * 70)
    sys.exit(0)
