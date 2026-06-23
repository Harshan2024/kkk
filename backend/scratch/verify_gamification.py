import urllib.request
import urllib.parse
import json
import sys

BASE_URL = "http://127.0.0.1:8001/api/v1/gamification"

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

def run_gamification_verification():
    print("Starting E2E verification of Gamification API...")
    
    # 1. Test GET /profile
    status, res = request_json(f"{BASE_URL}/profile?username=verify_user")
    print(f"GET /profile status: {status}")
    assert status == 200
    data = res.get("data", {})
    print(f"XP: {data.get('xp')}, Level: {data.get('level')}, Sustainability Score: {data.get('sustainability_score')}")
    
    # 2. Test GET /achievements
    status, res = request_json(f"{BASE_URL}/achievements?username=verify_user")
    print(f"GET /achievements status: {status}")
    assert status == 200
    print(f"Achievements Count: {len(res.get('data', []))}")
    
    # 3. Test GET /challenges
    status, res = request_json(f"{BASE_URL}/challenges?username=verify_user")
    print(f"GET /challenges status: {status}")
    assert status == 200
    print(f"Daily Challenges: {len(res.get('data', {}).get('daily', []))}")
    print(f"Weekly Challenges: {len(res.get('data', {}).get('weekly', []))}")
    
    # 4. Test GET /rewards
    status, res = request_json(f"{BASE_URL}/rewards?username=verify_user")
    print(f"GET /rewards status: {status}")
    assert status == 200
    rewards = res.get("data", [])
    print(f"Available Rewards Count: {len(rewards)}")
    
    # 5. Test POST /rewards/redeem (Failure cases / Balance check)
    status, res = request_json(f"{BASE_URL}/rewards/redeem", method="POST", data={"reward_id": "climate_cert", "username": "verify_user"})
    print(f"POST /rewards/redeem (expect insufficient funds) status: {status}")
    # User verify_user has 0 XP, cert costs 1000. Should get 400 Bad Request
    assert status == 400
    print(f"Error Message: {res.get('detail')}")
    
    print("\nAll Gamification API endpoints verified successfully!")

if __name__ == "__main__":
    run_gamification_verification()
