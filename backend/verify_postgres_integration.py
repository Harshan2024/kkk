import sys
import os
import traceback
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.session import engine, SessionLocal, Base
from app.models.models import User, Activity, Achievement
from app.models.activity_entity import ActivityEntity
from app.models.history import History
from app.models.analytics import Analytics
from app.models.coach_report import CoachReport
from app.history.history_service import HistoryService
from app.gamification.gamification_service import GamificationService

def run_verification():
    print("=" * 60)
    print("CarbonTracker -- PostgreSQL Integration Verification")
    print("=" * 60)
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    print()

    db = SessionLocal()
    username = f"verify_user_{str(int(time.time()))[-6:]}"
    user = None

    try:
        # 1. User Creation
        user = User(username=username, xp=10, level=1, redeemed_rewards=[])
        db.add(user)
        db.commit()
        db.refresh(user)
        print("[PASS] User creation persisted in PostgreSQL")

        # 2. Activity & Entity Persistence
        activity = Activity(
            user_id=user.id,
            input_text="I travelled 25 km by train",
            category="transport",
            item="train",
            quantity=25.0,
            unit="km",
            calculated_value=0.50,
            region="Global",
            metadata_json={"source": "manual"},
            logged_at=datetime.utcnow()
        )
        db.add(activity)
        db.commit()
        db.refresh(activity)

        entity = ActivityEntity(
            activity_id=activity.id,
            entity_name="train",
            entity_category="transport",
            quantity=25.0,
            unit="km",
            factor=0.02,
            carbon_emission=0.50
        )
        db.add(entity)
        db.commit()
        print("[PASS] Activity and Entity persisted in PostgreSQL")

        # 3. History Persistence
        hist = History(user_id=user.id, activity_id=activity.id, created_at=datetime.utcnow())
        db.add(hist)
        db.commit()
        print("[PASS] History row persisted in PostgreSQL")

        # Verify through HistoryService
        h_service = HistoryService()
        records = h_service.get_all(db=db)
        user_records = [r for r in records if r["id"] == str(hist.id)]
        assert len(user_records) == 1, "History record not found via HistoryService"
        print("[PASS] History retrieval via HistoryService from PostgreSQL verified")

        # 4. Analytics Persistence
        from app.repositories.analytics_repository import AnalyticsRepository
        analytics_repo = AnalyticsRepository(db)
        snapshot = analytics_repo.create_or_update(
            user_id=user.id,
            weekly_total=10.5,
            monthly_total=45.2,
            sustainability_score=92.0
        )
        assert snapshot.id is not None
        print("[PASS] Analytics snapshot persisted in PostgreSQL")

        # 5. AI Coach persistence
        from app.repositories.coach_repository import CoachRepository
        coach_repo = CoachRepository(db)
        report = coach_repo.create(
            user_id=user.id,
            report_type="weekly_summary",
            report_data={"summary": "Excellent week!", "score": 92.0}
        )
        assert report.id is not None
        print("[PASS] Coach report persisted in PostgreSQL")

        # 6. Marketplace Persistence (redeeming reward)
        g_service = GamificationService()
        # Ensure user has enough XP
        user.xp = 500
        db.commit()
        res = g_service.redeem_reward(username, "eco_avatar", db=db)
        assert "eco_avatar" in res["redeemed_rewards"]
        
        # Verify in DB
        db.refresh(user)
        assert "eco_avatar" in user.redeemed_rewards
        print("[PASS] Reward redemptions persisted in PostgreSQL (users table JSON field)")

        # 7. Achievement Persistence
        ach = Achievement(
            user_id=user.id,
            name="verification_milestone",
            description="Achieved verification",
            badge_type="bronze"
        )
        db.add(ach)
        db.commit()
        print("[PASS] Achievements persisted in PostgreSQL")

        print()
        print("=" * 60)
        print("VERIFICATION COMPLETED SUCCESSFULLY -- ALL PERSISTENCE VALIDATED")
        print("=" * 60)

    except Exception as e:
        print(f"[FAIL] Verification failed: {e}")
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Cleanup test user and cascade records
        if user:
            try:
                db.delete(user)
                db.commit()
                print("[CLEANUP] Verification test user cleaned up from PostgreSQL")
            except Exception as e:
                db.rollback()
                print(f"[WARN] Cleanup failed: {e}")
        db.close()

if __name__ == "__main__":
    run_verification()
