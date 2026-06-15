import time
import requests
import json

def measure_endpoint(name, url, expected_status=200):
    t0 = time.perf_counter()
    try:
        r = requests.get(url)
        elapsed = (time.perf_counter() - t0) * 1000
        print(f"{name:30} Status: {r.status_code} | Latency: {elapsed:8.2f}ms")
        if r.status_code == expected_status:
            try:
                data = r.json()
                if "performance_breakdown" in data:
                    print("  Performance Breakdown:")
                    print(f"    DB Query: {data['performance_breakdown'].get('db_query_duration_ms')}ms")
                    print(f"    Aggregation: {data['performance_breakdown'].get('aggregation_duration_ms')}ms")
                    print(f"    Total Backend: {data['performance_breakdown'].get('total_duration_ms')}ms")
                elif "data" in data and isinstance(data["data"], dict) and "performance_breakdown" in data["data"]:
                    pb = data["data"]["performance_breakdown"]
                    print("  Performance Breakdown (inside data):")
                    print(f"    DB Query: {pb.get('db_query_duration_ms')}ms")
                    print(f"    Aggregation: {pb.get('aggregation_duration_ms')}ms")
                    print(f"    Total Backend: {pb.get('total_duration_ms')}ms")
            except Exception:
                pass
        else:
            print(f"  [ERROR] Expected {expected_status}, got {r.status_code}")
        return elapsed
    except Exception as e:
        print(f"{name:30} Failed! Error: {e}")
        return None

if __name__ == "__main__":
    # Clear dashboard cache first if possible, or just query demo_user
    # Note: we query a new username to force an uncached run
    test_user = f"user_{int(time.time())}"
    print(f"Pinging endpoints for user: {test_user}")
    
    print("\n--- Warmup Run ---")
    measure_endpoint("System Status", "http://127.0.0.1:8001/api/system/status")
    measure_endpoint("Activities List", f"http://127.0.0.1:8001/api/v1/activities?username={test_user}")
    measure_endpoint("Dashboard Summary (Uncached)", f"http://127.0.0.1:8001/api/v1/dashboard/summary?username={test_user}")
    measure_endpoint("Habit Analysis", f"http://127.0.0.1:8001/api/v1/habit-analysis?username={test_user}")
    
    print("\n--- Second Run (Cached/Pooled) ---")
    measure_endpoint("System Status", "http://127.0.0.1:8001/api/system/status")
    measure_endpoint("Activities List", f"http://127.0.0.1:8001/api/v1/activities?username={test_user}")
    measure_endpoint("Dashboard Summary (Cached)", f"http://127.0.0.1:8001/api/v1/dashboard/summary?username={test_user}")
    measure_endpoint("Habit Analysis", f"http://127.0.0.1:8001/api/v1/habit-analysis?username={test_user}")
