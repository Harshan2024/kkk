import urllib.request
import json
import time

BASE_URL = "http://127.0.0.1:8001/api/v1"

def test_parse(text):
    url = f"{BASE_URL}/activities/parse?text={urllib.parse.quote(text)}&region=Global"
    print(f"\nRequest GET: {url}")
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode())
            print(f"Response (HTTP 200):")
            print(json.dumps(res, indent=2))
            return res
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"Response (HTTP {e.code}):")
        try:
            print(json.dumps(json.loads(body), indent=2))
        except:
            print(body)
        return {"status": "error", "error": f"HTTP {e.code}"}
    except Exception as e:
        print(f"Error: {e}")
        return {"status": "error", "error": str(e)}

def test_extract(text):
    url = f"{BASE_URL}/entities/extract?text={urllib.parse.quote(text)}"
    print(f"\nRequest GET: {url}")
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode())
            print(f"Response (HTTP 200):")
            print(json.dumps(res, indent=2))
            return res
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"Response (HTTP {e.code}):")
        try:
            print(json.dumps(json.loads(body), indent=2))
        except:
            print(body)
        return {"status": "error", "error": f"HTTP {e.code}"}
    except Exception as e:
        print(f"Error: {e}")
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    # Wait for server to be fully ready
    time.sleep(2)
    
    print("=" * 60)
    print("RUNNING API VERIFICATION PASS")
    print("=" * 60)
    
    # 1. Multi-food tests
    print("\n--- 1. MULTI-FOOD DETECTION ---")
    r = test_parse("I ate chicken biriyani and egg noodles")
    assert r.get("status") == "success"
    assert len(r.get("entities", [])) == 2
    assert r["entities"][0]["entity"].lower() == "chicken biriyani"
    assert r["entities"][1]["entity"].lower() == "egg noodles"
    
    r = test_parse("I ate 2 chicken biriyani, 1 egg noodles and 3 dosa")
    assert r.get("status") == "success"
    assert len(r.get("entities", [])) == 3
    assert r["entities"][0]["quantity"] == 2.0
    assert r["entities"][1]["quantity"] == 1.0
    assert r["entities"][2]["quantity"] == 3.0
    
    # 2. E-Waste Alias mapping
    print("\n--- 2. ELECTRONIC WASTE ALIAS MAPPING ---")
    r = test_parse("I recycled 1 kg electronic waste")
    assert r.get("status") == "success"
    assert r["entities"][0]["entity"].lower() == "e-waste"
    assert r["entities"][0]["factor"] == 12.0
    
    r = test_parse("I recycled 1 kg e-waste")
    assert r.get("status") == "success"
    assert r["entities"][0]["entity"].lower() == "e-waste"
    
    # 3. Entity Priority over Verbs
    print("\n--- 3. ENTITY PRIORITY OVER VERBS ---")
    # Entity must be electronic waste / E-Waste, not "recycled" or "recycling"
    r = test_parse("I recycled 1 kg electronic waste")
    assert r.get("status") == "success"
    assert r["entities"][0]["entity"].lower() == "e-waste"
    
    # 4. Formula Transparency
    print("\n--- 4. FORMULA TRANSPARENCY ---")
    r = test_parse("I disposed 2 kg plastic waste and 1 kg paper waste")
    assert r.get("status") == "success"
    assert len(r["entities"]) == 2
    assert r["entities"][0]["entity"].lower() == "plastic waste"
    assert r["entities"][0]["quantity"] == 2.0
    assert r["entities"][0]["factor"] == 6.0
    assert r["entities"][0]["formula"] == "2 x 6.0"
    assert r["entities"][0]["subtotal"] == 12.0
    assert r["entities"][1]["entity"].lower() == "paper waste"
    assert r["entities"][1]["quantity"] == 1.0
    assert r["entities"][1]["factor"] == 1.3
    assert r["entities"][1]["formula"] == "1 x 1.3"
    assert r["entities"][1]["subtotal"] == 1.3
    assert r["total_carbon"] == 13.3
    
    # 5. Unknown Entity handling
    print("\n--- 5. UNKNOWN ENTITY HANDLING ---")
    for unknown in ["spaceship", "alien food", "unknown material"]:
        r = test_parse(unknown)
        assert r.get("status") == "error"
        assert r.get("error") == "entity_not_found"
        assert r.get("entity") == "unknown"
        assert r.get("confidence") == 0.0

    print("\n" + "=" * 60)
    print("ALL API VERIFICATIONS PASSED SUCCESSFULLY!")
    print("=" * 60)
