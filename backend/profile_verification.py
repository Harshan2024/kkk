import sys
import os
import requests
import time
from datetime import datetime

# Setup path so we can access database session directly if needed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.session import SessionLocal, engine
from app.models.models import User
from app.models.user_profile import UserProfile

BASE_URL = "http://localhost:8001/api/v1"

def run_verification():
    print("=" * 65)
    print("CarbonTracker -- User Profile & Auth Integration Verification")
    print("=" * 65)
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    print()

    suffix = str(int(time.time()))[-6:]
    username = f"testprofile_{suffix}"
    email = f"testprofile_{suffix}@example.com"
    password = "Password123"

    token = None
    headers = {}

    try:
        # 1. Registration
        print("[STEP 1] Testing /auth/register...")
        reg_payload = {"username": username, "email": email, "password": password}
        reg_res = requests.post(f"{BASE_URL}/auth/register", json=reg_payload)
        assert reg_res.status_code == 200, f"Register failed: {reg_res.text}"
        assert reg_res.json()["success"] is True
        print("[PASS] User registration endpoint successfully verified.")

        # 2. Login
        print("\n[STEP 2] Testing /auth/login...")
        login_payload = {"email": email, "password": password}
        login_res = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        login_data = login_res.json()
        assert login_data["success"] is True
        token = login_data["data"]["access_token"]
        assert token is not None
        headers = {"Authorization": f"Bearer {token}"}
        print("[PASS] Login endpoint verified. JWT token successfully acquired.")

        # 3. JWT Protection and /auth/me
        print("\n[STEP 3] Testing /auth/me (JWT Protection)...")
        # Test without token first
        unauth_res = requests.get(f"{BASE_URL}/auth/me")
        assert unauth_res.status_code == 401, "Auth me did not enforce JWT check"
        # Test with token
        me_res = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        assert me_res.status_code == 200, f"Auth me call failed: {me_res.text}"
        assert me_res.json()["success"] is True
        assert me_res.json()["data"]["username"] == username
        print("[PASS] JWT protection and /auth/me successfully verified.")

        # 4. Profile Loading (GET /profile)
        print("\n[STEP 4] Testing GET /profile...")
        prof_res = requests.get(f"{BASE_URL}/profile", headers=headers)
        assert prof_res.status_code == 200, f"Get profile failed: {prof_res.text}"
        prof_data = prof_res.json()["data"]
        assert prof_data["username"] == username
        assert prof_data["email"] == email
        assert prof_data["full_name"] == "" # default empty
        print("[PASS] Profile loading endpoint successfully verified.")

        # 5. Profile Editing (PUT /profile)
        print("\n[STEP 5] Testing PUT /profile (Editing)...")
        update_payload = {
            "full_name": "Dr. Verification Expert",
            "phone_number": "+1 (555) 987-6543",
            "location": "San Francisco",
            "country": "United States",
            "college": "Stanford University",
            "department": "Sustainability Science",
            "bio": "Verifying database columns and endpoints in real-time."
        }
        put_res = requests.put(f"{BASE_URL}/profile", json=update_payload, headers=headers)
        assert put_res.status_code == 200, f"Update profile failed: {put_res.text}"
        updated_data = put_res.json()["data"]
        assert updated_data["full_name"] == "Dr. Verification Expert"
        assert updated_data["phone_number"] == "+1 (555) 987-6543"
        assert updated_data["location"] == "San Francisco"
        assert updated_data["college"] == "Stanford University"
        print("[PASS] Profile editing successfully verified via API update.")

        # 6. Database Persistence Verification
        print("\n[STEP 6] Querying PostgreSQL directly to verify persistence...")
        db = SessionLocal()
        db_user = db.query(User).filter(User.username == username).first()
        assert db_user is not None
        db_profile = db.query(UserProfile).filter(UserProfile.user_id == db_user.id).first()
        assert db_profile is not None
        assert db_profile.full_name == "Dr. Verification Expert"
        assert db_profile.phone_number == "+1 (555) 987-6543"
        assert db_profile.location == "San Francisco"
        assert db_profile.college == "Stanford University"
        db.close()
        print("[PASS] PostgreSQL persistence validated directly in DB.")

        # 7. Avatar Upload Verification (POST /profile/avatar)
        print("\n[STEP 7] Testing POST /profile/avatar...")
        # Create a tiny mock image content (1x1 pixel gif)
        gif_content = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
        files = {'file': ('avatar.gif', gif_content, 'image/gif')}
        avatar_res = requests.post(f"{BASE_URL}/profile/avatar", files=files, headers=headers)
        assert avatar_res.status_code == 200, f"Avatar upload failed: {avatar_res.text}"
        avatar_data = avatar_res.json()["data"]
        assert "/static/avatars/" in avatar_data["profile_picture"]
        print("[PASS] Avatar uploading endpoint verified. Served location mapped successfully.")

        print()
        print("=" * 65)
        print("VERIFICATION COMPLETED SUCCESSFULLY -- ALL PERSISTENCE VALIDATED")
        print("=" * 65)

    except Exception as e:
        print(f"[FAIL] Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Clean up database records
        print("\n[CLEANUP] Cleaning up integration test records from PostgreSQL...")
        db = SessionLocal()
        try:
            test_user = db.query(User).filter(User.username == username).first()
            if test_user:
                db.delete(test_user)
                db.commit()
                print("[CLEANUP] Deleted test user and cascaded profile records successfully.")
        except Exception as err:
            db.rollback()
            print(f"[WARN] Cleanup failed: {err}")
        finally:
            db.close()

if __name__ == "__main__":
    run_verification()
