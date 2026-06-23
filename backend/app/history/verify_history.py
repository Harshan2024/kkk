import urllib.request
import urllib.parse
import json
import sys

BASE_URL = "http://127.0.0.1:8001/api/v1"

def request_json(url, method="GET", data=None):
    req_data = None
    if data is not None:
        req_data = json.dumps(data).encode('utf-8')
    
    req = urllib.request.Request(url, data=req_data, method=method)
    req.add_header("Content-Type", "application/json")
    
    try:
        with urllib.request.urlopen(req) as response:
            body = response.read().decode('utf-8')
            return response.status, json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, body

def request_raw(url, method="GET"):
    req = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(req) as response:
        return response.status, response.read().decode('utf-8')

def run_e2e_verification():
    print("Starting e2e verification of History API...")
    
    # 1. Test POST /history with valid multi-entity input
    url_post = f"{BASE_URL}/history"
    record_payload = {
        "timestamp": "2026-06-23T10:15:00",
        "activities": [
            {
                "name": "Electric Train",
                "category": "transport",
                "quantity": 25,
                "unit": "km",
                "factor": 0.02,
                "carbon": 0.50
            },
            {
                "name": "Chicken Biriyani",
                "category": "food",
                "quantity": 2,
                "unit": "portion",
                "factor": 2.50,
                "carbon": 5.00
            }
        ],
        "source": "manual"
    }
    
    status, res = request_json(url_post, method="POST", data=record_payload)
    print(f"POST /history status: {status}")
    if status != 200:
        print(f"Error creating record: {res}")
        sys.exit(1)
        
    record = res.get("data", {})
    record_id = record.get("id")
    print(f"Created Record ID: {record_id}, Total Carbon: {record.get('total_carbon')}, Categories: {record.get('categories')}")
    assert record.get("total_carbon") == 5.5, "Total carbon calculation failed"
    assert record.get("categories") == ["food", "transport"], "Category extraction failed"
    
    # 2. Test GET /history/{id}
    url_get_id = f"{BASE_URL}/history/{record_id}"
    status, res = request_json(url_get_id)
    print(f"GET /history/{{id}} status: {status}")
    assert status == 200
    assert res.get("data", {}).get("id") == record_id
    
    # 3. Test validation errors: POST /history with negative carbon
    invalid_payload = {
        "timestamp": "2026-06-23T10:15:00",
        "activities": [
            {
                "name": "Electric Train",
                "category": "transport",
                "quantity": 25,
                "unit": "km",
                "factor": 0.02,
                "carbon": -0.50
            }
        ]
    }
    status, res = request_json(url_post, method="POST", data=invalid_payload)
    print(f"POST /history with negative carbon status: {status} (Expected 400)")
    assert status == 400
    
    # 4. Test GET /history (Search & Filter)
    url_list = f"{BASE_URL}/history?query=Biriyani"
    status, res = request_json(url_list)
    print(f"GET /history?query=Biriyani status: {status}")
    assert status == 200
    assert len(res.get("data", [])) >= 1
    
    # 5. Test GET /history/stats
    url_stats = f"{BASE_URL}/history/stats"
    status, res = request_json(url_stats)
    print(f"GET /history/stats status: {status}")
    assert status == 200
    stats = res.get("data", {})
    print(f"Stats: Total Activities={stats.get('total_activities')}, Total Carbon={stats.get('total_carbon')}")
    assert stats.get("total_activities") >= 2
    
    # 6. Test GET /history/export
    url_export_json = f"{BASE_URL}/history/export?format=json"
    status, res_json = request_raw(url_export_json)
    print(f"GET /history/export?format=json status: {status}")
    assert status == 200
    assert "Chicken Biriyani" in res_json
    
    url_export_csv = f"{BASE_URL}/history/export?format=csv"
    status, res_csv = request_raw(url_export_csv)
    print(f"GET /history/export?format=csv status: {status}")
    assert status == 200
    assert "record_id,timestamp,total_carbon" in res_csv
    assert "Chicken Biriyani" in res_csv
    
    # 7. Test PUT /history/{id}
    url_put = f"{BASE_URL}/history/{record_id}"
    update_payload = {
        "timestamp": "2026-06-23T10:15:00",
        "activities": [
            {
                "name": "Electric Train",
                "category": "transport",
                "quantity": 30,
                "unit": "km",
                "factor": 0.02,
                "carbon": 0.60
            }
        ]
    }
    status, res = request_json(url_put, method="PUT", data=update_payload)
    print(f"PUT /history/{{id}} status: {status}")
    if status != 200:
        print(f"PUT /history/{{id}} failed with response: {res}")
    assert status == 200
    assert res.get("data", {}).get("total_carbon") == 0.60
    
    # 8. Test DELETE /history/{id}
    status, res = request_json(url_put, method="DELETE")
    print(f"DELETE /history/{{id}} status: {status}")
    assert status == 200
    
    # 9. Verify deletion
    status, res = request_json(url_get_id)
    print(f"Verify deletion GET /history/{{id}} status: {status} (Expected 404)")
    assert status == 404
    
    print("\nAll endpoints verified successfully!")

if __name__ == "__main__":
    run_e2e_verification()
