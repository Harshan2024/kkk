"""
database_tests.py — CarbonTracker Database Test Suite (Phase I.1)
==================================================================
Verifies the full PostgreSQL schema & persistence foundation.

Tests:
  T01  Connection Success
  T02  Table Creation (all 6 Phase I.1 tables exist)
  T03  User Insert
  T04  User Read (by id + by username)
  T05  User Update (xp, level)
  T06  User Delete
  T07  Activity Insert
  T08  Activity Read
  T09  Activity FK (links to User)
  T10  ActivityEntity Insert
  T11  ActivityEntity FK (links to Activity)
  T12  ActivityEntity Read
  T13  History Insert + FK verification
  T14  Analytics Insert (create_or_update)
  T15  CoachReport Insert
  T16  CRUD — Update Activity
  T17  CRUD — Delete Activity (cascade to entities)
  T18  Rollback Handling

Usage:
    cd backend
    .venv\\Scripts\\python.exe database_tests.py
"""
import sys
import os
import traceback
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Force UTF-8 output on Windows to avoid cp1252 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# -- Colour helpers (optional, degrades gracefully on plain terminals) --------
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def ok(msg):  print(f"  {GREEN}[PASS]{RESET} {msg}")
def fail(msg):print(f"  {RED}[FAIL]{RESET} {msg}")
def warn(msg):print(f"  {YELLOW}[WARN]{RESET} {msg}")

# ── Results tracker ────────────────────────────────────────────────────────────
results = []

def run_test(test_id: str, description: str, fn):
    """Run a single test function, catch exceptions, record result."""
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


# ── Setup: import engine and session ──────────────────────────────────────────
from app.database.session import engine, SessionLocal, Base, OFFLINE_MODE
from app.models.models import User, Activity
from app.models.activity_entity import ActivityEntity
from app.models.history import History
from app.models.analytics import Analytics
from app.models.coach_report import CoachReport
from app.repositories.user_repository import UserRepository
from app.repositories.activity_repository import ActivityRepository
from app.repositories.history_repository import HistoryRepository
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.coach_repository import CoachRepository

# ── Test state (shared across tests in order) ──────────────────────────────────
_test_user_id   = None
_test_activity_id = None
_test_entity_id   = None
_test_history_id  = None
_test_analytics_id = None
_test_report_id   = None
_UNIQUE_SUFFIX = str(int(time.time()))[-6:]  # 6-digit suffix for unique names


# =============================================================================
# INDIVIDUAL TEST FUNCTIONS
# =============================================================================

def t01_connection():
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
    assert result == 1, f"Expected 1, got {result}"


def t02_tables_exist():
    from sqlalchemy import inspect as sa_inspect
    inspector = sa_inspect(engine)
    existing = set(inspector.get_table_names())
    required = {"users", "activities", "activity_entities", "history", "analytics", "coach_reports"}
    missing = required - existing
    assert not missing, f"Missing tables: {missing}"


def t03_user_insert():
    global _test_user_id
    db = SessionLocal()
    try:
        repo = UserRepository(db)
        user = repo.create(username=f"test_user_{_UNIQUE_SUFFIX}", xp=0, level=1)
        assert user.id is not None, "User id should not be None after insert"
        assert user.username == f"test_user_{_UNIQUE_SUFFIX}"
        assert user.xp == 0
        assert user.level == 1
        _test_user_id = user.id
    finally:
        db.close()


def t04_user_read():
    assert _test_user_id is not None, "t03 must pass first"
    db = SessionLocal()
    try:
        repo = UserRepository(db)
        by_id = repo.get_by_id(_test_user_id)
        assert by_id is not None, f"get_by_id({_test_user_id}) returned None"
        assert by_id.username == f"test_user_{_UNIQUE_SUFFIX}"

        by_name = repo.get_by_username(f"test_user_{_UNIQUE_SUFFIX}")
        assert by_name is not None, "get_by_username returned None"
        assert by_name.id == _test_user_id
    finally:
        db.close()


def t05_user_update():
    assert _test_user_id is not None
    db = SessionLocal()
    try:
        repo = UserRepository(db)
        updated = repo.update(_test_user_id, xp=150, level=3)
        assert updated is not None, "update returned None"
        assert updated.xp == 150, f"Expected xp=150, got {updated.xp}"
        assert updated.level == 3, f"Expected level=3, got {updated.level}"
    finally:
        db.close()


def t07_activity_insert():
    global _test_activity_id
    assert _test_user_id is not None
    db = SessionLocal()
    try:
        repo = ActivityRepository(db)
        act = repo.create_activity(
            user_id=_test_user_id,
            input_text="I travelled 25 km by train",
            category="transport",
            item="train",
            quantity=25.0,
            unit="km",
            calculated_value=0.50,
            region="Global",
        )
        assert act.id is not None, "Activity id should not be None"
        assert act.user_id == _test_user_id
        assert act.input_text == "I travelled 25 km by train"
        assert act.calculated_value == 0.50
        # Verify property aliases
        assert act.activity_text == "I travelled 25 km by train"
        assert act.total_carbon == 0.50
        _test_activity_id = act.id
    finally:
        db.close()


def t08_activity_read():
    assert _test_activity_id is not None
    db = SessionLocal()
    try:
        repo = ActivityRepository(db)
        act = repo.get_by_id(_test_activity_id)
        assert act is not None, f"get_by_id({_test_activity_id}) returned None"
        assert act.category == "transport"

        user_acts = repo.get_by_user(_test_user_id)
        assert any(a.id == _test_activity_id for a in user_acts), \
            "Activity not found in user activity list"
    finally:
        db.close()


def t09_activity_fk():
    """Confirm activity.user_id is a valid FK to users."""
    assert _test_activity_id is not None
    db = SessionLocal()
    try:
        act = db.query(Activity).filter(Activity.id == _test_activity_id).first()
        assert act is not None
        user = db.query(User).filter(User.id == act.user_id).first()
        assert user is not None, "FK from activities.user_id to users.id is broken"
        assert user.id == _test_user_id
    finally:
        db.close()


def t10_entity_insert():
    global _test_entity_id
    assert _test_activity_id is not None
    db = SessionLocal()
    try:
        repo = ActivityRepository(db)
        entity = repo.create_entity(
            activity_id=_test_activity_id,
            entity_name="Train",
            entity_category="transport",
            quantity=25.0,
            unit="km",
            factor=0.02,
            carbon_emission=0.50,
        )
        assert entity.id is not None, "ActivityEntity id should not be None"
        assert entity.activity_id == _test_activity_id
        assert entity.entity_name == "Train"
        assert entity.carbon_emission == 0.50
        _test_entity_id = entity.id
    finally:
        db.close()


def t11_entity_fk():
    """Confirm activity_entity.activity_id FK is valid."""
    assert _test_entity_id is not None
    db = SessionLocal()
    try:
        entity = db.query(ActivityEntity).filter(ActivityEntity.id == _test_entity_id).first()
        assert entity is not None
        act = db.query(Activity).filter(Activity.id == entity.activity_id).first()
        assert act is not None, "FK from activity_entities.activity_id to activities.id is broken"
        assert act.id == _test_activity_id
    finally:
        db.close()


def t12_entity_read():
    assert _test_activity_id is not None
    db = SessionLocal()
    try:
        repo = ActivityRepository(db)
        entities = repo.get_entities_for_activity(_test_activity_id)
        assert len(entities) >= 1, "Expected at least 1 entity"
        assert any(e.entity_name == "Train" for e in entities)
    finally:
        db.close()


def t13_history_insert_fk():
    global _test_history_id
    assert _test_user_id is not None and _test_activity_id is not None
    db = SessionLocal()
    try:
        repo = HistoryRepository(db)
        entry = repo.create(user_id=_test_user_id, activity_id=_test_activity_id)
        assert entry.id is not None, "History id should not be None"
        assert entry.user_id == _test_user_id
        assert entry.activity_id == _test_activity_id

        # Read back
        fetched = repo.get_by_id(entry.id)
        assert fetched is not None
        assert fetched.id == entry.id

        user_history = repo.get_by_user(_test_user_id)
        assert any(h.id == entry.id for h in user_history)
        _test_history_id = entry.id
    finally:
        db.close()


def t14_analytics_create_or_update():
    global _test_analytics_id
    assert _test_user_id is not None
    db = SessionLocal()
    try:
        repo = AnalyticsRepository(db)
        snap = repo.create_or_update(
            user_id=_test_user_id,
            weekly_total=4.2,
            monthly_total=18.5,
            sustainability_score=82.0,
        )
        assert snap.id is not None
        assert snap.weekly_total == 4.2
        assert snap.monthly_total == 18.5
        assert snap.sustainability_score == 82.0
        _test_analytics_id = snap.id

        # Update — should not create a second row
        updated = repo.create_or_update(
            user_id=_test_user_id,
            weekly_total=5.0,
        )
        assert updated.id == snap.id, "Upsert should update existing row, not create new"
        assert updated.weekly_total == 5.0
        assert updated.monthly_total == 18.5  # unchanged
    finally:
        db.close()


def t15_coach_report_insert():
    global _test_report_id
    assert _test_user_id is not None
    db = SessionLocal()
    try:
        repo = CoachRepository(db)
        report = repo.create(
            user_id=_test_user_id,
            report_type="weekly_summary",
            report_data={"insights": ["Reduce car usage"], "score": 82},
        )
        assert report.id is not None
        assert report.report_type == "weekly_summary"
        assert report.report_data["score"] == 82

        fetched = repo.get_by_id(report.id)
        assert fetched is not None
        assert fetched.id == report.id

        user_reports = repo.get_by_user(_test_user_id)
        assert any(r.id == report.id for r in user_reports)
        _test_report_id = report.id
    finally:
        db.close()


def t16_update_activity():
    assert _test_activity_id is not None
    db = SessionLocal()
    try:
        repo = ActivityRepository(db)
        updated = repo.update_activity(
            _test_activity_id,
            calculated_value=0.75,
        )
        assert updated is not None, "update_activity returned None"
        assert updated.calculated_value == 0.75, f"Expected 0.75, got {updated.calculated_value}"
    finally:
        db.close()


def t17_delete_activity_cascade():
    """Deleting an activity should cascade to its entities."""
    assert _test_activity_id is not None and _test_entity_id is not None
    db = SessionLocal()
    try:
        # Verify entity exists before delete
        entity_before = db.query(ActivityEntity).filter(ActivityEntity.id == _test_entity_id).first()
        assert entity_before is not None, "Entity should exist before cascade delete"

        repo = ActivityRepository(db)
        deleted = repo.delete_activity(_test_activity_id)
        assert deleted is True, "delete_activity should return True"

        # Activity should be gone
        gone = repo.get_by_id(_test_activity_id)
        assert gone is None, "Activity should be deleted"

        # Entity should also be gone (cascade)
        entity_after = db.query(ActivityEntity).filter(ActivityEntity.id == _test_entity_id).first()
        assert entity_after is None, "ActivityEntity should cascade-delete when Activity is deleted"
    finally:
        db.close()


def t18_rollback_handling():
    """Verify that a failed transaction rolls back cleanly without corrupting the session."""
    db = SessionLocal()
    try:
        # Force a duplicate username error (user with this name was created in t03)
        from sqlalchemy.exc import IntegrityError
        try:
            duplicate = User(username=f"test_user_{_UNIQUE_SUFFIX}", xp=0, level=1)
            db.add(duplicate)
            db.commit()
            fail_flag = False
        except IntegrityError:
            db.rollback()
            fail_flag = True

        assert fail_flag, "Expected IntegrityError for duplicate username was not raised"

        # Session should still be usable after rollback
        from sqlalchemy import text
        result = db.execute(text("SELECT 1")).scalar()
        assert result == 1, "Session unusable after rollback"
    finally:
        db.close()


def t06_user_delete():
    """Runs last — deletes the test user and verifies cascade."""
    assert _test_user_id is not None
    db = SessionLocal()
    try:
        repo = UserRepository(db)
        deleted = repo.delete(_test_user_id)
        assert deleted is True, "delete() should return True"

        gone = repo.get_by_id(_test_user_id)
        assert gone is None, "User should not exist after delete"

        # History entry for this user should be gone (cascade)
        if _test_history_id:
            hist = db.query(History).filter(History.id == _test_history_id).first()
            assert hist is None, "History should cascade-delete when User is deleted"
    finally:
        db.close()


# =============================================================================
# MAIN
# =============================================================================

def main():
    print()
    print(f"{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}CarbonTracker -- Phase I.1 Database Test Suite{RESET}")
    print(f"{'=' * 60}")
    print(f"Timestamp : {datetime.utcnow().isoformat()}Z")
    print()

    if OFFLINE_MODE:
        print(f"{RED}ERROR: Database is in OFFLINE_MODE. Set DATABASE_URL in .env.{RESET}")
        sys.exit(1)

    # Ensure tables exist before running tests
    from app.models import (ActivityEntity, History, Analytics, CoachReport)  # noqa: register
    Base.metadata.create_all(bind=engine)

    # ── Run tests in order ────────────────────────────────────────────────────
    run_test("T01", "Connection Success",               t01_connection)
    run_test("T02", "All 6 Phase I.1 tables exist",    t02_tables_exist)
    run_test("T03", "User Insert",                      t03_user_insert)
    run_test("T04", "User Read (by_id + by_username)",  t04_user_read)
    run_test("T05", "User Update (xp, level)",          t05_user_update)
    run_test("T07", "Activity Insert",                     t07_activity_insert)
    run_test("T08", "Activity Read",                       t08_activity_read)
    run_test("T09", "Activity FK -> User",                 t09_activity_fk)
    run_test("T10", "ActivityEntity Insert",               t10_entity_insert)
    run_test("T11", "ActivityEntity FK -> Activity",       t11_entity_fk)
    run_test("T12", "ActivityEntity Read",                 t12_entity_read)
    run_test("T13", "History Insert + FK",                 t13_history_insert_fk)
    run_test("T14", "Analytics create_or_update (upsert)", t14_analytics_create_or_update)
    run_test("T15", "CoachReport Insert + Read",           t15_coach_report_insert)
    run_test("T16", "CRUD - Update Activity",              t16_update_activity)
    run_test("T17", "CRUD - Delete Activity (cascade)",    t17_delete_activity_cascade)
    run_test("T18", "Rollback Handling",                   t18_rollback_handling)
    run_test("T06", "User Delete (cascade)",               t06_user_delete)

    # ── Summary ───────────────────────────────────────────────────────────────
    total  = len(results)
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
                    # Print only first 3 lines of traceback for readability
                    for line in detail.strip().splitlines()[:3]:
                        print(f"         {line}")
        print()
        sys.exit(1)
    else:
        print(f"\n{GREEN}[OK] All tests PASSED -- Phase I.1 database foundation verified.{RESET}")
        print()
        print("Tables confirmed in PostgreSQL carbontracker database:")
        print("  * users")
        print("  * activities")
        print("  * activity_entities")
        print("  * history")
        print("  * analytics")
        print("  * coach_reports")
        print()


if __name__ == "__main__":
    main()
