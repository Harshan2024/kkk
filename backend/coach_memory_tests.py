"""
coach_memory_tests.py -- CarbonTracker AI Coach Database Memory Test Suite (Phase I.4)
======================================================================================
Verifies all targets from Phase I.4 spec: Memory Persistence, Habit Detection,
Trend Analysis, Insight Generation, Recommendation Diversity, Goal Tracking,
Weekly/Monthly Reports, Chat Continuity, and PostgreSQL Persistence.
"""
import sys
import os
import unittest
from datetime import datetime, timedelta

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.session import SessionLocal, Base, engine
from app.models import (
    User, 
    Activity, 
    UserSustainabilityProfile, 
    Goal, 
    TrendRecord, 
    AIInsight, 
    CoachReport,
    SustainabilityScore
)
from app.coach.coach_memory_service import CoachMemoryService
from app.coach.habit_intelligence import HabitIntelligenceEngine
from app.coach.trend_memory import TrendMemoryEngine
from app.coach.insight_engine import CoachInsightEngine
from app.coach.goal_manager import GoalManager
from app.coach.recommendation_engine import generate_db_recommendations, generate_db_action_plan
from app.coach.coach_service import CoachService

class TestCoachDatabaseMemory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()
        # Ensure a clean test user exists
        cls.username = "test_coach_memory_user"
        cls.user = cls.db.query(User).filter(User.username == cls.username).first()
        if cls.user:
            cls.cleanup_database(cls.user.id)
            cls.db.delete(cls.user)
            cls.db.commit()
            
        cls.user = User(username=cls.username, xp=100, level=1)
        cls.db.add(cls.user)
        cls.db.commit()
        cls.db.refresh(cls.user)
        cls.user_id = cls.user.id

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "user_id"):
            cls.cleanup_database(cls.user_id)
            user = cls.db.query(User).filter(User.id == cls.user_id).first()
            if user:
                cls.db.delete(user)
                cls.db.commit()
        cls.db.close()

    @classmethod
    def cleanup_database(cls, user_id: int):
        cls.db.query(Activity).filter(Activity.user_id == user_id).delete()
        cls.db.query(UserSustainabilityProfile).filter(UserSustainabilityProfile.user_id == user_id).delete()
        cls.db.query(Goal).filter(Goal.user_id == user_id).delete()
        cls.db.query(TrendRecord).filter(TrendRecord.user_id == user_id).delete()
        cls.db.query(AIInsight).filter(AIInsight.user_id == user_id).delete()
        cls.db.query(CoachReport).filter(CoachReport.user_id == user_id).delete()
        cls.db.query(SustainabilityScore).filter(SustainabilityScore.user_id == user_id).delete()
        cls.db.commit()

    def test_01_memory_persistence(self):
        """Verify activities can be successfully saved and queried."""
        # Insert transport and food activities
        act1 = Activity(
            user_id=self.user_id,
            input_text="commuted 15 km by car",
            category="transport",
            item="car",
            quantity=15.0,
            unit="km",
            calculated_value=2.88,
            logged_at=datetime.utcnow() - timedelta(days=2)
        )
        act2 = Activity(
            user_id=self.user_id,
            input_text="had beef burger",
            category="food",
            item="beef",
            quantity=0.25,
            unit="kg",
            calculated_value=15.0,
            logged_at=datetime.utcnow() - timedelta(days=1)
        )
        self.db.add(act1)
        self.db.add(act2)
        self.db.commit()

        acts = self.db.query(Activity).filter(Activity.user_id == self.user_id).all()
        self.assertEqual(len(acts), 2)
        self.assertIn("car", [a.item for a in acts])

    def test_02_habit_detection(self):
        """Verify HabitIntelligenceEngine updates sustainability profile and saves habit insight."""
        hi = HabitIntelligenceEngine(self.db)
        res = hi.analyze_and_update(self.user_id, self.username)
        
        self.assertIn("food_profile", res)
        self.assertIn("overall_maturity", res)

        profile = self.db.query(UserSustainabilityProfile).filter(
            UserSustainabilityProfile.user_id == self.user_id
        ).first()
        self.assertIsNotNone(profile)
        self.assertEqual(profile.overall_maturity, "Eco Beginner")

        insight = self.db.query(AIInsight).filter(
            AIInsight.user_id == self.user_id,
            AIInsight.insight_type == "habit"
        ).first()
        self.assertIsNotNone(insight)
        self.assertIn("Food profile", insight.content)

    def test_03_trend_analysis(self):
        """Verify TrendMemoryEngine computes 30/60/90 trends and consistency evolution."""
        tm = TrendMemoryEngine(self.db)
        res = tm.track_trends(self.user_id)
        
        self.assertEqual(len(res), 3) # 30, 60, 90 day trends
        self.assertTrue(all(t.user_id == self.user_id for t in res))

        trend_rec = self.db.query(TrendRecord).filter(
            TrendRecord.user_id == self.user_id,
            TrendRecord.period_days == 30
        ).first()
        self.assertIsNotNone(trend_rec)
        self.assertIsNotNone(trend_rec.consistency_evolution)

    def test_04_insight_generation(self):
        """Verify CoachInsightEngine savesPositive, Risk, and Improvement insights."""
        ie = CoachInsightEngine(self.db)
        insights = ie.generate_and_save_insights(self.user_id)
        
        self.assertEqual(len(insights), 5)
        insight_types = [ins.insight_type for ins in insights]
        self.assertIn("positive", insight_types)
        self.assertIn("risk", insight_types)
        self.assertIn("improvement", insight_types)

    def test_05_recommendation_diversity(self):
        """Verify generate_db_recommendations enforces diversity and scores categories."""
        # Clean coach reports first
        self.db.query(CoachReport).filter(CoachReport.user_id == self.user_id).delete()
        self.db.commit()

        # Call recommendations
        recs = generate_db_recommendations(self.db, self.user_id)
        self.assertTrue(len(recs) > 0)
        
        # Save a coach report with the top recommendation to simulate previous list
        top_rec = recs[0]
        rep = CoachReport(
            user_id=self.user_id,
            report_type="weekly_summary",
            report_data={"recommendations": [top_rec]}
        )
        self.db.add(rep)
        self.db.commit()

        # Generate again: the top recommendation should be demoted and not be first, ensuring diversity
        new_recs = generate_db_recommendations(self.db, self.user_id)
        self.assertNotEqual(new_recs[0], top_rec)

    def test_06_goal_tracking(self):
        """Verify GoalManager creates goals, tracks progress, and auto-completes when target met."""
        gm = GoalManager(self.db)
        # Create an activity logging goal (target is 1 activity)
        goal = gm.create_goal(
            user_id=self.user_id,
            goal_type="activity",
            target_value=1.0,
            target_date=datetime.utcnow() + timedelta(days=1)
        )
        self.assertEqual(goal.status, "active")
        self.assertEqual(goal.progress_percentage, 0.0)


        # Log one more activity to make total 3 (since we logged 2 in test 1)
        act3 = Activity(
            user_id=self.user_id,
            input_text="recycled paper",
            category="waste",
            item="paper",
            quantity=1.0,
            unit="kg",
            calculated_value=0.1,
            logged_at=datetime.utcnow()
        )
        self.db.add(act3)
        self.db.commit()

        # Update goal progress
        gm.update_goal_progress(self.user_id)
        
        updated_goal = self.db.query(Goal).filter(Goal.id == goal.id).first()
        self.assertEqual(updated_goal.status, "completed")
        self.assertEqual(updated_goal.progress_percentage, 100.0)

    def test_07_weekly_and_monthly_reports(self):
        """Verify WeeklyReport and MonthlyReport generate and persist in database."""
        cs = CoachService()
        w_rep = cs.get_weekly_report(self.user_id, self.db)
        m_rep = cs.get_monthly_report(self.user_id, self.db)

        self.assertIsNotNone(w_rep)
        self.assertIsNotNone(m_rep)
        
        weekly_db = self.db.query(CoachReport).filter(
            CoachReport.user_id == self.user_id,
            CoachReport.report_type == "weekly_summary"
        ).first()
        self.assertIsNotNone(weekly_db)

        monthly_db = self.db.query(CoachReport).filter(
            CoachReport.user_id == self.user_id,
            CoachReport.report_type == "monthly_summary"
        ).first()
        self.assertIsNotNone(monthly_db)

    def test_08_chat_continuity(self):
        """Verify coach dialogue answer queries using database stats and advice."""
        cs = CoachService()
        res = cs.answer_chat_query("analyze my habits", self.user_id, self.db)
        
        self.assertIn("Habit Analysis Report", res)
        self.assertIn("Food Profile", res)
        self.assertIn("Transport Profile", res)

        # Query goals
        res_goals = cs.answer_chat_query("check my goals", self.user_id, self.db)
        self.assertIn("Goals", res_goals)

if __name__ == "__main__":
    unittest.main()
