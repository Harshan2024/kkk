"""
activity_persistence_tests.py -- CarbonTracker Activity Persistence Test Suite (Phase I.2)
===========================================================================================
Verifies that activities, entities, history, and analytics are all persisted
correctly to PostgreSQL via the persistence_service layer.

Tests:
  T01  Connection + baseline counts
  T02  Activity row insert via ActivityRepository
  T03  ActivityEntity row created via persistence_service
  T04  History row created via persistence_service
  T05  Analytics snapshot upserted via persistence_service
  T06  Foreign key: activity_entity.activity_id -> activities.id
  T07  Foreign key: history.activity_id -> activities.id
  T08  Foreign key: history.user_id -> users.id
  T09  Multi-entity: compound activity creates multiple entities
  T10  Analytics incremental update (second activity increases totals)
  T11  Rollback: failed entity insert does not break history step
  T12  Repository CRUD: update + delete activity
  T13  PostgreSQL persistence: counts must be > 0 after inserts
  T14  End-to-end: "I travelled 25 km by train, ate 2 chicken biriyani
       and used AC 1500W for 3 hours" -> 3 activities, 3 entities, 3 history rows

Usage:
    cd backend
    .venv\\Scripts\\python.exe activity_persistence_tests.py
"""
import sys
import os
import traceback
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
def warn(msg): print(f"  {YELLOW}[WARN]{RESET} {msg}")

results = []
_SUFFIX = str(int(time.time()))[-6:]

def run_test(test_id, description, fn):
    try:
        fn()
        ok(f"[{test_id}] {description}")
        results.append((test_id, "PASS", description, None))
    except AssertionError as e:
        fail(f"[{test_id}] {description} -- AssertionError: {e}")
        results.append((test_id, "FAIL", description, str(e)))
    except Exception as e:
        fail(f"[{test_id}] {description} -- {type(e).__name__}: {e}")
        results.append((test_id, "ERROR", description, traceback.format_exc()))


# ── Imports ───────────────────────────────────────────────────────────────────
from app.database.session import engine, SessionLocal, Base, OFFLINE_MODE
from app.models.models import User, Activity
from app.models.activity_entity import ActivityEntity
from app.models.history import History
from app.models.analytics import Analytics
from app.repositories.user_repository import UserRepository
from app.repositories.activity_repository import ActivityRepository
from app.repositories.history_repository import HistoryRepository
from app.repositories.analytics_repository import AnalyticsRepository
from app.services.persistence_service import save_activity_persistence

# ── Shared state ──────────────────────────────────────────────────────────────
_user_id      = None
_activity_id  = None
_entity_id    = None
_history_id   = None
_analytics_id = None
_baseline_activities = 0
_baseline_entities   = 0
_baseline_history    = 0

# =============================================================================
# TEST IMPLEMENTATIONS
# =============================================================================

def t01_connection_and_baseline():
    global _baseline_activities, _baseline_entities, _baseline_history
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text("SELECT 1")).scalar()
    db = SessionLocal()
    try:
        _baseline_activities = db.query(Activity).count()
        _baseline_entities   = db.query(ActivityEntity).count()
        _baseline_history    = db.query(History).count()
        print(f"      Baseline: activities={_baseline_activities} entities={_baseline_entities} history={_baseline_history}")
    finally:
        db.close()


def t02_activity_insert():
    global _user_id, _activity_id
    db = SessionLocal()
    try:
        # Ensure user exists
        user_repo = UserRepository(db)
        user = user_repo.get_by_username(f"persist_test_{_SUFFIX}")
        if not user:
            user = user_repo.create(username=f"persist_test_{_SUFFIX}", xp=0, level=1)
        _user_id = user.id

        act_repo = ActivityRepository(db)
        act = act_repo.create_activity(
            user_id=_user_id,
            input_text="I travelled 25 km by train",
            category="transport",
            item="train",
            quantity=25.0,
            unit="km",
            calculated_value=0.725,
            region="Global",
        )
        assert act.id is not None
        assert act.calculated_value == 0.725
        _activity_id = act.id
    finally:
        db.close()


def t03_entity_via_persistence_service():
    global _entity_id
    assert _user_id is not None and _activity_id is not None
    db = SessionLocal()
    try:
        act = db.query(Activity).filter(Activity.id == _activity_id).first()
        parsed_part = {
            "item": "train",
            "category": "transport",
            "quantity": 25.0,
            "unit": "km",
        }
        metadata = {"emission_factor": 0.029, "formula": "25 x 0.029"}

        count_before = db.query(ActivityEntity).filter(ActivityEntity.activity_id == _activity_id).count()
        save_activity_persistence(db, _user_id, act, parsed_part, metadata)
        count_after = db.query(ActivityEntity).filter(ActivityEntity.activity_id == _activity_id).count()

        assert count_after == count_before + 1, f"Expected {count_before + 1} entities, got {count_after}"

        entity = db.query(ActivityEntity).filter(ActivityEntity.activity_id == _activity_id).first()
        assert entity is not None
        assert entity.entity_name == "train"
        assert entity.entity_category == "transport"
        _entity_id = entity.id
    finally:
        db.close()


def t04_history_via_persistence_service():
    global _history_id
    assert _user_id is not None and _activity_id is not None
    db = SessionLocal()
    try:
        hist_count_before = db.query(History).filter(
            History.user_id == _user_id, History.activity_id == _activity_id
        ).count()
        # History was already created in t03 call to save_activity_persistence
        hist = db.query(History).filter(
            History.user_id == _user_id, History.activity_id == _activity_id
        ).first()
        assert hist is not None, "History row should exist after save_activity_persistence"
        assert hist.user_id == _user_id
        assert hist.activity_id == _activity_id
        _history_id = hist.id
    finally:
        db.close()


def t05_analytics_upserted():
    global _analytics_id
    assert _user_id is not None
    db = SessionLocal()
    try:
        snap = db.query(Analytics).filter(Analytics.user_id == _user_id).first()
        assert snap is not None, "Analytics snapshot should exist after save_activity_persistence"
        assert snap.weekly_total >= 0.0
        assert snap.monthly_total >= 0.0
        assert 0.0 <= snap.sustainability_score <= 100.0
        _analytics_id = snap.id
    finally:
        db.close()


def t06_fk_entity_to_activity():
    assert _entity_id is not None and _activity_id is not None
    db = SessionLocal()
    try:
        entity = db.query(ActivityEntity).filter(ActivityEntity.id == _entity_id).first()
        assert entity is not None
        act = db.query(Activity).filter(Activity.id == entity.activity_id).first()
        assert act is not None, "FK: activity_entities.activity_id -> activities.id is broken"
        assert act.id == _activity_id
    finally:
        db.close()


def t07_fk_history_to_activity():
    assert _history_id is not None and _activity_id is not None
    db = SessionLocal()
    try:
        hist = db.query(History).filter(History.id == _history_id).first()
        assert hist is not None
        act = db.query(Activity).filter(Activity.id == hist.activity_id).first()
        assert act is not None, "FK: history.activity_id -> activities.id is broken"
        assert act.id == _activity_id
    finally:
        db.close()


def t08_fk_history_to_user():
    assert _history_id is not None and _user_id is not None
    db = SessionLocal()
    try:
        hist = db.query(History).filter(History.id == _history_id).first()
        assert hist is not None
        user = db.query(User).filter(User.id == hist.user_id).first()
        assert user is not None, "FK: history.user_id -> users.id is broken"
        assert user.id == _user_id
    finally:
        db.close()


def t09_multi_entity_compound():
    """Three distinct parsed parts -> three ActivityEntity rows on one Activity."""
    assert _user_id is not None
    db = SessionLocal()
    try:
        act_repo = ActivityRepository(db)

        # Create one compound activity
        compound_act = act_repo.create_activity(
            user_id=_user_id,
            input_text="I travelled 25 km by train, ate 2 chicken biriyani and used AC 1500W for 3 hours",
            category="transport",
            item="compound",
            quantity=1.0,
            unit="unit",
            calculated_value=6.0,
        )

        parts = [
            {"item": "train",            "category": "transport",   "quantity": 25.0, "unit": "km"},
            {"item": "chicken_biriyani", "category": "food",        "quantity": 2.0,  "unit": "plate"},
            {"item": "ac",               "category": "appliances",  "quantity": 3.0,  "unit": "hours"},
        ]
        metas = [
            {"emission_factor": 0.029},
            {"food_co2_kg": 1.785},
            {"emission_factor": 0.7},
        ]

        entity_count_before = db.query(ActivityEntity).filter(
            ActivityEntity.activity_id == compound_act.id
        ).count()

        for p, m in zip(parts, metas):
            save_activity_persistence(db, _user_id, compound_act, p, m)

        entity_count_after = db.query(ActivityEntity).filter(
            ActivityEntity.activity_id == compound_act.id
        ).count()

        # Each call to save_activity_persistence adds 1 entity + 1 history
        assert entity_count_after == entity_count_before + 3, (
            f"Expected {entity_count_before + 3} entities, got {entity_count_after}"
        )

        # Verify entity names
        entities = db.query(ActivityEntity).filter(
            ActivityEntity.activity_id == compound_act.id
        ).all()
        entity_names = {e.entity_name for e in entities}
        assert "train"            in entity_names, f"'train' not found in {entity_names}"
        assert "chicken_biriyani" in entity_names, f"'chicken_biriyani' not found in {entity_names}"
        assert "ac"               in entity_names, f"'ac' not found in {entity_names}"
    finally:
        db.close()


def t10_analytics_incremental_update():
    """A second activity increases the analytics totals."""
    assert _user_id is not None and _analytics_id is not None
    db = SessionLocal()
    try:
        snap_before = db.query(Analytics).filter(Analytics.id == _analytics_id).first()
        weekly_before = snap_before.weekly_total

        # Insert another activity and trigger analytics update
        act_repo = ActivityRepository(db)
        act = act_repo.create_activity(
            user_id=_user_id,
            input_text="Ate chicken biriyani",
            category="food",
            item="chicken_biriyani",
            quantity=1.0,
            unit="plate",
            calculated_value=1.785,
        )
        save_activity_persistence(db, _user_id, act, {"item": "chicken_biriyani", "category": "food", "quantity": 1.0, "unit": "plate"}, {"food_co2_kg": 1.785})

        # Refresh snapshot
        db.expire(snap_before)
        snap_after = db.query(Analytics).filter(Analytics.user_id == _user_id).first()
        assert snap_after.weekly_total > weekly_before, (
            f"Expected weekly_total to increase: {weekly_before} -> {snap_after.weekly_total}"
        )
    finally:
        db.close()


def t11_rollback_does_not_break_session():
    """After a simulated failure the session remains usable."""
    from sqlalchemy.exc import IntegrityError
    db = SessionLocal()
    try:
        # Force a duplicate-username integrity error
        try:
            dup = User(username=f"persist_test_{_SUFFIX}", xp=0, level=1)
            db.add(dup)
            db.commit()
            rolled = False
        except IntegrityError:
            db.rollback()
            rolled = True

        assert rolled, "Expected IntegrityError for duplicate username"

        # Session should still work
        from sqlalchemy import text
        result = db.execute(text("SELECT 1")).scalar()
        assert result == 1, "Session unusable after rollback"
    finally:
        db.close()


def t12_crud_update_delete():
    assert _activity_id is not None
    db = SessionLocal()
    try:
        act_repo = ActivityRepository(db)

        # Update
        updated = act_repo.update_activity(_activity_id, calculated_value=0.99)
        assert updated is not None
        assert updated.calculated_value == 0.99

        # Create a throw-away activity and delete it
        throwaway = act_repo.create_activity(
            user_id=_user_id,
            input_text="throwaway for delete test",
            category="lifestyle",
            item="unknown",
            quantity=1.0,
            unit="unit",
            calculated_value=0.0,
        )
        throwaway_id = throwaway.id
        deleted = act_repo.delete_activity(throwaway_id)
        assert deleted is True
        assert act_repo.get_by_id(throwaway_id) is None
    finally:
        db.close()


def t13_postgresql_counts_nonzero():
    """After all inserts, activity/entity/history tables must have data."""
    db = SessionLocal()
    try:
        act_count  = db.query(Activity).count()
        ent_count  = db.query(ActivityEntity).count()
        hist_count = db.query(History).count()
        anal_count = db.query(Analytics).count()

        print(f"      activities={act_count}  activity_entities={ent_count}  history={hist_count}  analytics={anal_count}")

        assert act_count  > _baseline_activities, f"activities count ({act_count}) not > baseline ({_baseline_activities})"
        assert ent_count  > _baseline_entities,   f"activity_entities count ({ent_count}) not > baseline ({_baseline_entities})"
        assert hist_count > _baseline_history,    f"history count ({hist_count}) not > baseline ({_baseline_history})"
        assert anal_count > 0, "analytics table is still empty"
    finally:
        db.close()


def t14_end_to_end_compound():
    """
    Full end-to-end: simulate the compound sentence test.
    Input: 'I travelled 25 km by train, ate 2 chicken biriyani and used AC 1500W for 3 hours'
    Expected: 3 activities, 3 entities, 3 history rows (from this test session).
    """
    assert _user_id is not None
    db = SessionLocal()
    try:
        act_repo  = ActivityRepository(db)
        hist_repo = HistoryRepository(db)

        compound_inputs = [
            {"input_text": "I travelled 25 km by train", "category": "transport", "item": "train",            "quantity": 25.0, "unit": "km",    "value": 0.725,  "factor": 0.029},
            {"input_text": "ate 2 chicken biriyani",     "category": "food",      "item": "chicken_biriyani", "quantity": 2.0,  "unit": "plate", "value": 3.570,  "factor": 1.785},
            {"input_text": "used AC 1500W for 3 hours",  "category": "appliances","item": "ac",               "quantity": 3.0,  "unit": "hours", "value": 2.100,  "factor": 0.700},
        ]

        act_ids = []
        for ci in compound_inputs:
            act = act_repo.create_activity(
                user_id=_user_id,
                input_text=ci["input_text"],
                category=ci["category"],
                item=ci["item"],
                quantity=ci["quantity"],
                unit=ci["unit"],
                calculated_value=ci["value"],
                region="Global",
            )
            parsed  = {"item": ci["item"], "category": ci["category"], "quantity": ci["quantity"], "unit": ci["unit"]}
            meta    = {"emission_factor": ci["factor"]}
            save_activity_persistence(db, _user_id, act, parsed, meta)
            act_ids.append(act.id)

        # Verify entities and history created for each activity
        for aid in act_ids:
            entities = db.query(ActivityEntity).filter(ActivityEntity.activity_id == aid).all()
            assert len(entities) >= 1, f"No entity row for activity_id={aid}"

            hist_rows = db.query(History).filter(
                History.activity_id == aid, History.user_id == _user_id
            ).all()
            assert len(hist_rows) >= 1, f"No history row for activity_id={aid}"

        # Analytics should reflect all 3
        snap = db.query(Analytics).filter(Analytics.user_id == _user_id).first()
        assert snap is not None
        expected_weekly_min = sum(ci["value"] for ci in compound_inputs) * 0.5  # conservative
        assert snap.weekly_total >= expected_weekly_min, (
            f"weekly_total ({snap.weekly_total:.3f}) seems too low for the inserted activities"
        )

        total_carbon = sum(ci["value"] for ci in compound_inputs)
        print(f"      3 activities inserted. Total carbon: {total_carbon:.3f} kgCO2e")
        print(f"      Analytics weekly_total: {snap.weekly_total:.3f} kgCO2e")
    finally:
        db.close()


def teardown_test_user():
    """Remove the test user and all cascade-deleted rows."""
    if _user_id is None:
        return
    db = SessionLocal()
    try:
        user_repo = UserRepository(db)
        user_repo.delete(_user_id)
        print(f"\n  [CLEANUP] Test user id={_user_id} and all cascade data removed.")
    except Exception as e:
        print(f"\n  [CLEANUP WARNING] Could not remove test user id={_user_id}: {e}")
    finally:
        db.close()


# =============================================================================
# MAIN
# =============================================================================
def main():
    print()
    print(f"{BOLD}{'=' * 62}{RESET}")
    print(f"{BOLD}CarbonTracker -- Phase I.2 Activity Persistence Test Suite{RESET}")
    print(f"{'=' * 62}")
    print(f"Timestamp : {datetime.utcnow().isoformat()}Z")
    print()

    if OFFLINE_MODE:
        print(f"{RED}ERROR: Database is in OFFLINE_MODE. Set DATABASE_URL in .env.{RESET}")
        sys.exit(1)

    # Ensure tables exist
    from app.models import ActivityEntity, History, Analytics, CoachReport  # noqa: register
    Base.metadata.create_all(bind=engine)

    run_test("T01", "Connection + baseline counts",                  t01_connection_and_baseline)
    run_test("T02", "Activity Insert via ActivityRepository",         t02_activity_insert)
    run_test("T03", "ActivityEntity created via persistence_service", t03_entity_via_persistence_service)
    run_test("T04", "History row created via persistence_service",    t04_history_via_persistence_service)
    run_test("T05", "Analytics snapshot upserted",                    t05_analytics_upserted)
    run_test("T06", "FK: activity_entity.activity_id -> activities",  t06_fk_entity_to_activity)
    run_test("T07", "FK: history.activity_id -> activities",          t07_fk_history_to_activity)
    run_test("T08", "FK: history.user_id -> users",                   t08_fk_history_to_user)
    run_test("T09", "Multi-entity compound (3 entities on 1 act)",    t09_multi_entity_compound)
    run_test("T10", "Analytics incremental update",                   t10_analytics_incremental_update)
    run_test("T11", "Rollback: session survives integrity error",      t11_rollback_does_not_break_session)
    run_test("T12", "CRUD: update + delete Activity",                 t12_crud_update_delete)
    run_test("T13", "PostgreSQL counts > 0 after all inserts",        t13_postgresql_counts_nonzero)
    run_test("T14", "End-to-end compound sentence (3-part activity)", t14_end_to_end_compound)

    # Cleanup test data
    teardown_test_user()

    # ── Summary ───────────────────────────────────────────────────────────────
    total  = len(results)
    passed = sum(1 for _, s, _, _ in results if s == "PASS")
    failed = sum(1 for _, s, _, _ in results if s in ("FAIL", "ERROR"))

    print()
    print(f"{'=' * 62}")
    print(f"{BOLD}Results: {passed}/{total} tests passed{RESET}")
    print(f"{'=' * 62}")

    if failed:
        print(f"\n{RED}FAILED TESTS:{RESET}")
        for tid, status, desc, detail in results:
            if status in ("FAIL", "ERROR"):
                print(f"  [{tid}] {desc}")
                if detail:
                    for line in detail.strip().splitlines()[:4]:
                        print(f"         {line}")
        print()
        sys.exit(1)
    else:
        print(f"\n{GREEN}[OK] All {total} tests PASSED -- Phase I.2 persistence verified.{RESET}")
        print()
        print("Verified PostgreSQL tables (rows must be > 0):")
        print("  * activities      -- Activity rows created and committed")
        print("  * activity_entities -- Entity rows linked to activities")
        print("  * history           -- History rows linking users to activities")
        print("  * analytics         -- Snapshot upserted with weekly/monthly totals")
        print()


if __name__ == "__main__":
    main()
