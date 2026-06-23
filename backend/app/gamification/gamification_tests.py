import unittest
import time
from datetime import datetime, timedelta
from app.history.history_repository import HistoryRepository
from app.history.history_service import HistoryService
from app.gamification.gamification_repository import GamificationRepository
from app.gamification.gamification_service import GamificationService

class TestGamificationSystem(unittest.TestCase):
    def setUp(self):
        self.test_history_file = "test_gamification_history.json"
        self.test_gamification_file = "test_gamification_rewards.json"
        import os
        for f in [self.test_history_file, self.test_gamification_file]:
            if os.path.exists(f):
                os.remove(f)
                
        self.hist_repo = HistoryRepository(file_path=self.test_history_file)
        self.history_service = HistoryService(repository=self.hist_repo)
        self.gam_repo = GamificationRepository(file_path=self.test_gamification_file)
        self.gam_service = GamificationService(
            history_service=self.history_service,
            repository=self.gam_repo
        )

    def tearDown(self):
        import os
        for f in [self.test_history_file, self.test_gamification_file]:
            if os.path.exists(f):
                os.remove(f)

    def test_xp_engine_activities(self):
        # 1. Log veggie food (food base 20 + veggie bonus 20 = 40 XP, plus first_log achievement bonus 50 + low_carbon_day bonus 100 + daily_veg_meal challenge bonus 50 + record base 20 = 240 XP)
        self.history_service.create_record({
            "timestamp": datetime.utcnow().isoformat(),
            "activities": [
                {"name": "Salad Meal", "category": "food", "quantity": 1.0, "unit": "portion", "factor": 0.5, "carbon": 0.5}
            ]
        })
        profile = self.gam_service.get_profile("test_user")
        self.assertEqual(profile.xp, 240)
        self.assertEqual(profile.level, 1)

    def test_streak_engine(self):
        # Log consecutive days
        now = datetime.utcnow()
        for i in range(3):
            ts = (now - timedelta(days=i)).isoformat()
            self.history_service.create_record({
                "timestamp": ts,
                "activities": [
                    {"name": "Bus Trip", "category": "transport", "quantity": 5.0, "unit": "km", "factor": 0.05, "carbon": 0.25}
                ]
            })
            
        profile = self.gam_service.get_profile("test_user")
        self.assertEqual(profile.streak, 3)
        # Streak 3 awards streak_3 achievement (100 XP) and streak 3 milestone (100 XP)
        self.assertTrue(profile.xp > 200)

    def test_achievement_engine(self):
        self.history_service.create_record({
            "timestamp": datetime.utcnow().isoformat(),
            "activities": [
                {"name": "Recycling Paper", "category": "waste", "quantity": 1.0, "unit": "kg", "factor": 0.1, "carbon": 0.1}
            ]
        })
        achievements = self.gam_service.get_achievements("test_user")
        first_log = next(a for a in achievements if a.id == "first_log")
        self.assertTrue(first_log.unlocked)
        self.assertEqual(first_log.progress, 1.0)

    def test_sustainability_score(self):
        # Log high emissions
        self.history_service.create_record({
            "timestamp": datetime.utcnow().isoformat(),
            "activities": [
                {"name": "Petrol Car Drive", "category": "transport", "quantity": 200.0, "unit": "km", "factor": 0.25, "carbon": 50.0}
            ]
        })
        profile = self.gam_service.get_profile("test_user")
        self.assertLess(profile.sustainability_score, 100.0)

    def test_challenge_engine(self):
        # Log veggie meal today
        self.history_service.create_record({
            "timestamp": datetime.utcnow().isoformat(),
            "activities": [
                {"name": "Salad", "category": "food", "quantity": 1.0, "unit": "portion", "factor": 0.5, "carbon": 0.5}
            ]
        })
        challenges = self.gam_service.get_challenges("test_user")
        veg_challenge = next(c for c in challenges["daily"] if c.id == "daily_veg_meal")
        self.assertTrue(veg_challenge.completed)
        self.assertEqual(veg_challenge.progress, 1.0)

    def test_rewards_redemption(self):
        # Log multiple items to gather XP
        for i in range(5):
            self.history_service.create_record({
                "timestamp": datetime.utcnow().isoformat(),
                "activities": [
                    {"name": "Bus Trip", "category": "transport", "quantity": 10.0, "unit": "km", "factor": 0.05, "carbon": 0.5}
                ]
            })
            
        profile_before = self.gam_service.get_profile("test_user")
        self.assertTrue(profile_before.available_xp >= 100)
        
        # Redeem Eco Avatar (Cost: 100 XP)
        res = self.gam_service.redeem_reward("test_user", "eco_avatar")
        self.assertEqual(res["status"], "success")
        
        profile_after = self.gam_service.get_profile("test_user")
        self.assertEqual(profile_after.available_xp, profile_before.available_xp - 100)
        self.assertTrue("eco_avatar" in profile_after.redeemed_rewards)
        
        # Double checkout guard check
        with self.assertRaises(ValueError):
            self.gam_service.redeem_reward("test_user", "eco_avatar")

    def test_latency(self):
        start = time.perf_counter()
        self.gam_service.get_profile("test_user")
        dur = (time.perf_counter() - start) * 1000
        self.assertLess(dur, 100.0)

if __name__ == "__main__":
    unittest.main()
