import subprocess
import time
import urllib.request
import urllib.error
import json
import sys
import os

print("==================================================")
print("RUNNING CarbonTracker AI - PRODUCTION HARDENING INTEGRATION TESTS")
print("==================================================")

# Port to run the test server on
TEST_PORT = 8006
url_base = f"http://127.0.0.1:{TEST_PORT}"

# Command to launch the server
cmd = [
    r".venv\Scripts\python.exe",
    "-m", "uvicorn",
    "app.main:app",
    "--host", "127.0.0.1",
    "--port", str(TEST_PORT)
]

print(f"Launching test backend on port {TEST_PORT} with database disconnected and ENVIRONMENT=production...")
current_dir = os.path.abspath(os.getcwd())
print(f"Current working directory: {current_dir}")
env = {
    **os.environ,
    "ENVIRONMENT": "production",
    "DATABASE_URL": "postgresql://postgres:wrongpassword@localhost:5439/nonexistent_db",
    "PYTHONPATH": current_dir
}

# Redirect output to a log file
log_file_path = os.path.join(current_dir, "scratch", "server_test.log")
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
log_file = open(log_file_path, "w", encoding="utf-8")

# Start server process
proc = subprocess.Popen(
    cmd,
    stdout=log_file,
    stderr=subprocess.STDOUT,
    text=True,
    env=env,
    cwd=current_dir
)

# Poll the server until it starts responding or times out (up to 60 seconds)
server_started = False
max_wait = 60
print(f"Polling server at {url_base}/ for up to {max_wait} seconds to allow connection retries to time out...")
for i in range(max_wait // 2):
    time.sleep(2)
    # Check if the process died early
    ret_code = proc.poll()
    if ret_code is not None:
        print(f"Test server process died early with exit code: {ret_code}")
        break
        
    try:
        response = urllib.request.urlopen(f"{url_base}/", timeout=1)
        if response.getcode() == 200:
            print(f"Server is up and running after {i*2 + 2} seconds!")
            server_started = True
            break
    except Exception:
        # Expected while server is starting
        pass

if not server_started:
    print("WARNING: Server did not respond within timeout. Proceeding to run test requests anyway to capture exact errors.")

tests_passed = True

def check_endpoint(path, method="GET", data=None, expected_status=200):
    global tests_passed
    url = f"{url_base}{path}"
    print(f"\n[Test] {method} {url}")
    
    req = urllib.request.Request(url, method=method, data=data)
    if data:
        req.add_header("Content-Type", "application/json")
        
    try:
        response = urllib.request.urlopen(req, timeout=5)
        code = response.getcode()
        body = response.read().decode()
        print(f"  Response Status: {code}")
        print(f"  Response Body: {body}")
        if code != expected_status:
            print(f"  [ERROR] FAILED: Expected status {expected_status}, got {code}")
            tests_passed = False
        else:
            print("  [SUCCESS] PASSED")
        return code, body
    except urllib.error.HTTPError as e:
        code = e.code
        body = e.read().decode()
        print(f"  Response Status: {code}")
        print(f"  Response Body: {body}")
        if code != expected_status:
            print(f"  [ERROR] FAILED: Expected status {expected_status}, got {code}")
            tests_passed = False
        else:
            print("  [SUCCESS] PASSED")
        return code, body
    except Exception as e:
        print(f"  [ERROR] FAILED: Request failed: {e}")
        tests_passed = False
        return None, None

try:
    check_endpoint("/", "GET", expected_status=200)
    check_endpoint("/api/v1/seed", "POST", data=b'{}', expected_status=403)
    code, body = check_endpoint("/debug-error", "GET", expected_status=500)
    if body:
        try:
            body_json = json.loads(body)
            if body_json.get("success") is not False or "error" not in body_json:
                print("  [ERROR] FAILED: Response JSON does not match the safe format.")
                tests_passed = False
        except Exception:
            tests_passed = False

    code, body = check_endpoint("/api/system/status", "GET", expected_status=200)
    if body:
        try:
            status_json = json.loads(body)
            db_status = status_json.get("data", {}).get("database")
            print(f"  Parsed Database Status: {db_status}")
            if db_status not in ("offline", "offline_safe_mode"):
                print(f"  [ERROR] FAILED: Database status should be offline or offline_safe_mode, got: {db_status}")
                tests_passed = False
        except Exception:
            tests_passed = False

finally:
    # Terminate server
    print("\nShutting down test backend server...")
    proc.terminate()
    proc.wait()
    log_file.close()
    
    try:
        # Read file output
        with open(log_file_path, "r", encoding="utf-8") as f:
            stdout_content = f.read()
            
        print("\n--- ALL TEST SERVER LOGS ---")
        structured_logs_count = 0
        unstructured_logs_count = 0
        for line in stdout_content.splitlines():
            line_strip = line.strip()
            print(f"  [Server Log] {line_strip}")
            if line_strip.startswith("{") and line_strip.endswith("}"):
                structured_logs_count += 1
            else:
                unstructured_logs_count += 1
                
        print(f"\n  Total JSON structured logs: {structured_logs_count}")
        print(f"  Total legacy unstructured logs: {unstructured_logs_count}")
        if structured_logs_count == 0:
            print("  [ERROR] FAILED: No JSON structured logs found in stdout.")
            tests_passed = False
    except Exception as e:
        print(f"Error clean-up: {e}")

if tests_passed:
    print("\n==================================================")
    print("ALL STABILITY SPRINT 1 SECURITY & LOGGING TESTS PASSED")
    print("==================================================")
    sys.exit(0)
else:
    print("\n==================================================")
    print("SOME SECURITY OR RESILIENCY TESTS FAILED")
    print("==================================================")
    sys.exit(1)
