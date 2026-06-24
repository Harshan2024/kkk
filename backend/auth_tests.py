"""
auth_tests.py — CarbonTracker Authentication Test Suite (Phase J)
==================================================================
Verifies password hashing, JWT encoding/decoding, user registration, 
login authentication, password resets, and user data isolation.

Usage:
    cd backend
    .venv\\Scripts\\python.exe auth_tests.py
"""
import sys
import os
import traceback
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Force UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def ok(msg):   print(f"  {GREEN}[PASS]{RESET} {msg}")
def fail(msg): print(f"  {RED}[FAIL]{RESET} {msg}")

results = []

def run_test(test_id: str, description: str, fn):
    try:
        fn()
        ok(f"[{test_id}] {description}")
        results.append((test_id, "PASS", description, None))
    except AssertionError as e:
        fail(f"[{test_id}] {description} — AssertionError: {e}")
        results.append((test_id, "FAIL", description, str(e)))
    except Exception as e:
        fail(f"[{test_id}] {description} — {type(e).__name__}: {e}")
        results.append((test_id, "ERROR", description, traceback.format_exc()))

# Setup: imports
from app.database.session import SessionLocal, Base, engine
from app.models.models import User
from app.auth.password_service import PasswordService
from app.auth.jwt_service import JWTService, get_current_user
from app.auth.auth_service import AuthService
from app.auth.auth_models import UserRegisterRequest, UserLoginRequest, ProfileUpdateRequest
from fastapi import HTTPException

# Test state
_UNIQUE_SUFFIX = str(int(time.time()))[-6:]
_test_username = f"auth_test_user_{_UNIQUE_SUFFIX}"
_test_email = f"auth_test_{_UNIQUE_SUFFIX}@example.com"
_test_password = "Password123!"
_reset_token = None

# =============================================================================
# INDIVIDUAL TEST FUNCTIONS
# =============================================================================

def t01_password_service():
    # 1. Hashing and verification
    hashed = PasswordService.hash_password(_test_password)
    assert hashed != _test_password, "Hash must not equal plaintext"
    assert PasswordService.verify_password(_test_password, hashed), "Valid password must verify"
    assert not PasswordService.verify_password("WrongPassword!", hashed), "Invalid password must not verify"

    # 2. Strength checks
    assert not PasswordService.validate_password_strength("Short1!"), "Should reject short passwords (less than 8 chars)"
    assert not PasswordService.validate_password_strength("NoDigits!"), "Should reject passwords without digits"
    assert not PasswordService.validate_password_strength("nouppercase1!"), "Should reject passwords without uppercase"
    assert PasswordService.validate_password_strength("ValidPass123!"), "Should accept valid password"

def t02_jwt_service():
    test_data = {"sub": _test_username, "role": "user"}
    
    # 1. Access token
    access_token = JWTService.create_access_token(test_data, expires_delta=timedelta(minutes=5))
    assert access_token is not None, "Access token should not be None"
    
    payload = JWTService.decode_token(access_token)
    assert payload is not None, "Decoded payload should not be None"
    assert payload.get("sub") == _test_username
    assert payload.get("role") == "user"

    # 2. Expiration
    expired_token = JWTService.create_access_token(test_data, expires_delta=timedelta(seconds=-5))
    expired_payload = JWTService.decode_token(expired_token)
    assert expired_payload is None, "Expired token should return None payload"

def t03_registration_and_login():
    db = SessionLocal()
    try:
        auth_service = AuthService(db)
        
        # 1. Register User
        payload = UserRegisterRequest(username=_test_username, email=_test_email, password=_test_password)
        user = auth_service.register_user(payload)
        assert user.id is not None, "Registered user must have an id"
        assert user.username == _test_username
        assert user.email == _test_email

        # 2. Duplicate Check
        try:
            auth_service.register_user(payload)
            assert False, "Should raise exception for duplicate registration"
        except HTTPException as e:
            assert e.status_code == 400, f"Expected 400 status, got {e.status_code}"

        # 3. Successful Login
        login_payload = UserLoginRequest(email=_test_email, password=_test_password)
        token_data = auth_service.login_user(login_payload)
        assert "access_token" in token_data, "Login response must contain access_token"
        assert "refresh_token" in token_data, "Login response must contain refresh_token"

        # 4. Invalid Password Login
        try:
            auth_service.login_user(UserLoginRequest(email=_test_email, password="WrongPassword!"))
            assert False, "Should reject login with invalid credentials"
        except HTTPException as e:
            assert e.status_code == 401, f"Expected 401 status, got {e.status_code}"
    finally:
        db.close()

def t04_protected_route_and_isolation():
    db = SessionLocal()
    try:
        # Fetch registered user
        user = db.query(User).filter(User.username == _test_username).first()
        assert user is not None, "User should be found in DB"

        # 1. Enforce user context helper test
        from app.api.endpoints import enforce_user_context
        
        # Matches: should pass
        username_result = enforce_user_context(_test_username, user)
        assert username_result == _test_username
        
        # Default/None: should resolve to user's username
        username_result_none = enforce_user_context(None, user)
        assert username_result_none == _test_username
        
        # Mismatch: should raise 403 Forbidden
        try:
            enforce_user_context("malicious_user", user)
            assert False, "enforce_user_context should block mismatched username queries"
        except HTTPException as e:
            assert e.status_code == 403, f"Expected 403 Forbidden, got {e.status_code}"

        # 2. Dependency test
        # Generate token
        token = JWTService.create_access_token({"sub": _test_username})
        resolved_user = get_current_user(db=db, token=token)
        assert resolved_user.id == user.id, "get_current_user must resolve user by token sub payload"
        
        # Invalid token
        try:
            get_current_user(db=db, token="invalid-token-value")
            assert False, "Should raise 401 for invalid token signature"
        except HTTPException as e:
            assert e.status_code == 401, f"Expected 401, got {e.status_code}"
    finally:
        db.close()

def t05_password_reset_flow():
    global _reset_token
    db = SessionLocal()
    try:
        auth_service = AuthService(db)
        
        # 1. Request Reset
        res = auth_service.request_reset(_test_email)
        assert "token" in res, "Reset request must return a token"
        _reset_token = res["token"]

        # 2. Confirm Reset
        new_pass = "NewPassword123!"
        success = auth_service.confirm_reset(_reset_token, new_pass)
        assert success is True, "Password reset confirmation should be True"

        # 3. Test Login with New Password
        login_payload = UserLoginRequest(email=_test_email, password=new_pass)
        token_data = auth_service.login_user(login_payload)
        assert "access_token" in token_data, "Should login successfully with new password"
    finally:
        db.close()

def t06_profile_endpoints():
    db = SessionLocal()
    try:
        auth_service = AuthService(db)
        user = db.query(User).filter(User.username == _test_username).first()
        assert user is not None

        # 1. Get Profile
        profile = auth_service.get_profile(user)
        assert profile["username"] == _test_username
        assert profile["email"] == _test_email
        assert "xp" in profile
        assert "level" in profile

        # 2. Update Profile
        updated_username = f"upd_{_test_username}"[:20]  # limit to username length
        updated_email = f"upd_{_test_email}"
        update_payload = ProfileUpdateRequest(username=updated_username, email=updated_email)
        
        updated_user = auth_service.update_profile(user, update_payload)
        assert updated_user.username == updated_username
        assert updated_user.email == updated_email

        # Verify in DB
        db.refresh(user)
        assert user.username == updated_username
        assert user.email == updated_email
    finally:
        db.close()

def main():
    print(f"{'=' * 60}")
    print(f"{BOLD}Running CarbonTracker Auth & Multi-User System Tests{RESET}")
    print(f"{'=' * 60}")

    run_test("T01", "Password Hashing & Strength Check",  t01_password_service)
    run_test("T02", "JWT Token Generation & Expiration",  t02_jwt_service)
    run_test("T03", "User Registration & Login (API/Service)", t03_registration_and_login)
    run_test("T04", "Protected Route Guard & User Isolation", t04_protected_route_and_isolation)
    run_test("T05", "Password Reset Workflow",            t05_password_reset_flow)
    run_test("T06", "Profile Loading & Update",           t06_profile_endpoints)

    # Clean up test user to keep db tidy
    db = SessionLocal()
    try:
        for u in db.query(User).filter(User.email.like("%auth_test_%")):
            db.delete(u)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

    total = len(results)
    passed = sum(1 for _, s, _, _ in results if s == "PASS")
    failed = sum(1 for _, s, _, _ in results if s in ("FAIL", "ERROR"))

    print()
    print(f"{'=' * 60}")
    print(f"{BOLD}Results: {passed}/{total} tests passed{RESET}")
    print(f"{'=' * 60}")

    if failed:
        print(f"\n{RED}FAILED TESTS:{RESET}")
        for tid, status, desc, detail in results:
            if status in ("FAIL", "ERROR"):
                print(f"  [{tid}] {desc}")
                if detail:
                    for line in detail.strip().splitlines()[:5]:
                        print(f"         {line}")
        print()
        sys.exit(1)
    else:
        print(f"\n{GREEN}[OK] All auth tests PASSED -- Phase J authentication layer verified.{RESET}\n")

if __name__ == "__main__":
    main()
