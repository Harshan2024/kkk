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

def run_coach_verification():
    print("Starting E2E verification of Coach API...")
    
    # 1. Register some activities in history first to ensure there is data to analyze
    print("Seeding dummy activities to history...")
    url_history = f"{BASE_URL}/history"
    history_payload = {
        "timestamp": "2026-06-23T10:15:00",
        "activities": [
            {
                "name": "AC 1500W",
                "category": "energy",
                "quantity": 5.0,
                "unit": "hours",
                "factor": 1.23,
                "carbon": 6.15
            },
            {
                "name": "Chicken Biriyani",
                "category": "food",
                "quantity": 2,
                "unit": "portions",
                "factor": 2.50,
                "carbon": 5.00
            },
            {
                "name": "Petrol Car",
                "category": "transport",
                "quantity": 10.0,
                "unit": "km",
                "factor": 0.20,
                "carbon": 2.00
            }
        ],
        "source": "manual"
    }
    status, res = request_json(url_history, method="POST", data=history_payload)
    print(f"POST /history status: {status}")
    if status != 200:
        print(f"Error seeding history: {res}")
        sys.exit(1)
        
    record_id = res.get("data", {}).get("id")
    print(f"Seeded record ID: {record_id}")
    
    # 2. Test GET /coach/analysis
    url_analysis = f"{BASE_URL}/coach/analysis"
    status, res = request_json(url_analysis)
    print(f"GET /coach/analysis status: {status}")
    assert status == 200
    data = res.get("data", {})
    print(f"Energy finding: {data.get('energy', {}).get('finding')}")
    print(f"Food profile: {data.get('food', {}).get('food_profile')}")
    print(f"Transport profile: {data.get('transport', {}).get('transport_profile')}")
    
    # 3. Test GET /coach/report/weekly
    url_weekly = f"{BASE_URL}/coach/report/weekly"
    status, res = request_json(url_weekly)
    print(f"GET /coach/report/weekly status: {status}")
    assert status == 200
    data = res.get("data", {})
    print(f"Weekly Carbon: {data.get('weekly_carbon')}, Top Source: {data.get('top_source')}")
    
    # 4. Test GET /coach/report/monthly
    url_monthly = f"{BASE_URL}/coach/report/monthly"
    status, res = request_json(url_monthly)
    print(f"GET /coach/report/monthly status: {status}")
    assert status == 200
    data = res.get("data", {})
    print(f"Monthly Carbon: {data.get('monthly_carbon')}, Achievements: {data.get('achievements')}")
    
    # 5. Test POST /coach/chat
    url_chat = f"{BASE_URL}/coach/chat"
    chat_payload = {"message": "Analyze my habits"}
    status, res = request_json(url_chat, method="POST", data=chat_payload)
    print(f"POST /coach/chat status: {status}")
    assert status == 200
    reply = res.get("data", {}).get("response", "")
    print(f"Coach Reply snippet:\n{reply[:150].encode('ascii', errors='replace').decode('ascii')}...")
    
    # Clean up the seeded history record
    url_delete = f"{BASE_URL}/history/{record_id}"
    status, _ = request_json(url_delete, method="DELETE")
    print(f"Cleaned up seeded record status: {status}")
    
    print("\nAll AI Sustainability Coach API endpoints verified successfully!")

if __name__ == "__main__":
    run_coach_verification()
