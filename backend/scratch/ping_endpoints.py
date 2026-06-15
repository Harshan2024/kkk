import time
import requests

def test_endpoint(name, url):
    t0 = time.perf_counter()
    try:
        r = requests.get(url)
        elapsed = (time.perf_counter() - t0) * 1000
        print(f"{name:30} Status: {r.status_code} | Latency: {elapsed:8.2f}ms")
        return elapsed
    except Exception as e:
        print(f"{name:30} Failed! Error: {e}")
        return None

print("Checking first DB Health...")
test_endpoint("DB Health 1", "http://127.0.0.1:8000/api/health/database")

print("Checking second DB Health immediately...")
test_endpoint("DB Health 2 (Cached)", "http://127.0.0.1:8000/api/health/database")
