import urllib.request
import urllib.error
import json

PORT = 8001
BASE_URL = f"http://127.0.0.1:{PORT}/api/v1"

def debug_auth():
    print("Sending registration...")
    url = f"{BASE_URL}/auth/register"
    data = {
        "username": "debug_user",
        "email": "debug_user@example.com",
        "password": "debug_password_123"
    }
    data_bytes = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, method="POST", data=data_bytes, headers={"Content-Type": "application/json"})
    
    try:
        with urllib.request.urlopen(req) as res:
            print("Status:", res.status)
            print("Body:", res.read().decode())
    except urllib.error.HTTPError as e:
        print("HTTP Error Status:", e.code)
        print("HTTP Error Body:", e.read().decode())
    except Exception as e:
        print("Network/Other Error:", e)

if __name__ == "__main__":
    debug_auth()
