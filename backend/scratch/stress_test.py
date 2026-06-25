#!/usr/bin/env python3
"""
stress_test.py
==============
CarbonTracker AI - Concurrent Stress Testing Script.
Simulates concurrent user behavior to verify rate limits, connection pool safety, and endpoint latencies under load.
"""
import sys
import os
import time
import json
import random
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

PORT = 8001
BASE_URL = f"http://127.0.0.1:{PORT}/api/v1"

# Shared statistics collector
stats = {
    "total_requests": 0,
    "success_count": 0,
    "rate_limited_count": 0,
    "bad_request_count": 0,
    "server_error_count": 0,
    "network_error_count": 0,
    "latencies": []
}

def send_request(url, method="GET", headers=None, data=None):
    if headers is None:
        headers = {}
    if data:
        data_bytes = json.dumps(data).encode('utf-8')
        headers["Content-Type"] = "application/json"
    else:
        data_bytes = None
        
    req = urllib.request.Request(url, method=method, data=data_bytes, headers=headers)
    t_start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            latency = (time.perf_counter() - t_start) * 1000.0
            body = response.read().decode('utf-8')
            return response.status, body, latency
    except urllib.error.HTTPError as e:
        latency = (time.perf_counter() - t_start) * 1000.0
        try:
            body = e.read().decode('utf-8')
        except Exception:
            body = ""
        return e.code, body, latency
    except Exception as e:
        latency = (time.perf_counter() - t_start) * 1000.0
        return 999, str(e), latency

def worker_task(user_idx, action_type, user_tokens):
    username = f"stress_user_{user_idx}"
    token = user_tokens.get(username)
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    url = ""
    method = "GET"
    data = None
    
    if action_type == "activity":
        url = f"{BASE_URL}/activities"
        method = "POST"
        data = {
            "text": f"Drove {random.randint(10, 100)} km by petrol car",
            "username": username,
            "region": "Global"
        }
    elif action_type == "analytics":
        url = f"{BASE_URL}/analytics?username={username}"
        method = "GET"
    elif action_type == "coach":
        url = f"{BASE_URL}/coach/analysis?username={username}"
        method = "GET"
    elif action_type == "marketplace":
        url = f"{BASE_URL}/gamification/rewards?username={username}"
        method = "GET"
        
    status, body, latency = send_request(url, method, headers, data)
    return status, latency

def main():
    print("==================================================")
    print("STARTING CARBONTRACKER CONCURRENT STRESS TEST")
    print("==================================================")
    
    # 1. Register and login test users
    print("[*] Setting up 10 test users and acquiring access tokens...")
    user_tokens = {}
    
    for i in range(10):
        username = f"stress_user_{i}"
        email = f"stress_user_{i}@example.com"
        password = "StressPassword123"
        
        # Register (allow already registered)
        send_request(
            f"{BASE_URL}/auth/register", 
            "POST", 
            data={"username": username, "email": email, "password": password}
        )
        
        # Login
        code, body, _ = send_request(
            f"{BASE_URL}/auth/login", 
            "POST", 
            data={"email": email, "password": password}
        )
        
        if code == 200:
            try:
                res_data = json.loads(body)
                token = res_data.get("data", {}).get("access_token")
                if token:
                    user_tokens[username] = token
            except Exception:
                pass

    print(f"[+] Successfully authenticated {len(user_tokens)} test users.")
    
    if not user_tokens:
        print("[-] Error: No authenticated users. Exiting.")
        sys.exit(1)

    # 2. Build task list matching load limits
    # Total tasks: 1000 activities, 500 analytics, 500 coach, 200 marketplace
    tasks = []
    for _ in range(1000):
        tasks.append((random.randint(0, 9), "activity"))
    for _ in range(500):
        tasks.append((random.randint(0, 9), "analytics"))
    for _ in range(500):
        tasks.append((random.randint(0, 9), "coach"))
    for _ in range(200):
        tasks.append((random.randint(0, 9), "marketplace"))
        
    random.shuffle(tasks)
    total_tasks = len(tasks)
    
    print(f"[*] Queueing {total_tasks} total concurrent requests...")
    print(f"[*] Dispatching with 100 worker threads...")
    
    t_start = time.perf_counter()
    
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = {
            executor.submit(worker_task, user_idx, action, user_tokens): (user_idx, action)
            for user_idx, action in tasks
        }
        
        for future in as_completed(futures):
            status, latency = future.result()
            stats["total_requests"] += 1
            stats["latencies"].append(latency)
            
            if status == 200:
                stats["success_count"] += 1
            elif status == 429:
                stats["rate_limited_count"] += 1
            elif status == 400:
                stats["bad_request_count"] += 1
            elif status == 500:
                stats["server_error_count"] += 1
            else:
                stats["network_error_count"] += 1

    duration = time.perf_counter() - t_start
    avg_latency = sum(stats["latencies"]) / len(stats["latencies"]) if stats["latencies"] else 0.0
    
    print("\n==================================================")
    print("STRESS TEST RESULTS SUMMARY")
    print("==================================================")
    print(f"Total Requests Executed : {stats['total_requests']}")
    print(f"Success Count (200 OK)  : {stats['success_count']}")
    print(f"Rate Limited (429)      : {stats['rate_limited_count']}")
    print(f"Bad Requests (400)      : {stats['bad_request_count']}")
    print(f"Server Errors (500)     : {stats['server_error_count']}")
    print(f"Network/Other Errors    : {stats['network_error_count']}")
    print(f"Total Execution Time    : {duration:.2f} seconds")
    print(f"Average Request Latency : {avg_latency:.2f} ms")
    print(f"Request Throughput      : {stats['total_requests'] / duration:.2f} req/sec")
    print("==================================================")
    
    # Save metrics to a file for readiness report ingestion
    metrics_file = os.path.join(os.path.dirname(__file__), "stress_test_metrics.json")
    with open(metrics_file, "w") as f:
        json.dump({
            "total_requests": stats["total_requests"],
            "success_count": stats["success_count"],
            "rate_limited": stats["rate_limited_count"],
            "bad_request": stats["bad_request_count"],
            "server_error": stats["server_error_count"],
            "network_error": stats["network_error_count"],
            "total_time_seconds": round(duration, 2),
            "average_latency_ms": round(avg_latency, 2),
            "throughput_req_sec": round(stats["total_requests"] / duration, 2)
        }, f, indent=2)
    print(f"[+] Metrics successfully exported to: {metrics_file}")

if __name__ == "__main__":
    main()
