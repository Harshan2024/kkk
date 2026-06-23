import unittest
import time
from datetime import datetime, timedelta
from app.coach.coach_service import CoachService
from app.history.history_repository import HistoryRepository
from app.history.history_service import HistoryService

class TestAICoachSystem(unittest.TestCase):
    def setUp(self):
        self.test_file = "test_coach_history.json"
        import os
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
            
        self.repo = HistoryRepository(file_path=self.test_file)
        self.history_service = HistoryService(repository=self.repo)
        self.coach_service = CoachService(history_service=self.history_service)

    def tearDown(self):
        import os
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_habit_detection_energy(self):
        # Log high AC usage (>4 hours/day)
        self.history_service.create_record({
            "timestamp": "2026-06-23T10:00:00",
            "activities": [
                {"name": "AC 1500W", "category": "energy", "quantity": 6.0, "unit": "hours", "factor": 1.2, "carbon": 7.2}
            ]
        })
        
        analysis = self.coach_service.get_analysis()
        self.assertEqual(analysis.energy.ac_hours, 6.0)
        self.assertEqual(analysis.energy.ac_percentage, 100.0)
        self.assertTrue("high_ac_usage" in [p.pattern for p in analysis.patterns])

    def test_habit_detection_food(self):
        # Log high meat consumption (Chicken Biriyani)
        self.history_service.create_record({
            "timestamp": "2026-06-23T12:00:00",
            "activities": [
                {"name": "Chicken Biriyani", "category": "food", "quantity": 2.0, "unit": "portions", "factor": 2.5, "carbon": 5.0}
            ]
        })
        
        analysis = self.coach_service.get_analysis()
        self.assertEqual(analysis.food.food_profile, "high_meat_consumption")
        self.assertEqual(analysis.food.animal_ratio, 1.0)
        self.assertEqual(analysis.food.veg_ratio, 0.0)
        self.assertTrue("high_meat_intake" in [p.pattern for p in analysis.patterns])

    def test_habit_detection_transport(self):
        # Log private driver (mostly car)
        self.history_service.create_record({
            "timestamp": "2026-06-23T14:00:00",
            "activities": [
                {"name": "Petrol Car", "category": "transport", "quantity": 50.0, "unit": "km", "factor": 0.2, "carbon": 10.0}
            ]
        })
        
        analysis = self.coach_service.get_analysis()
        self.assertEqual(analysis.transport.transport_profile, "private_driver")
        self.assertEqual(analysis.transport.public_transport_ratio, 0.0)

    def test_habit_detection_waste(self):
        # Log high plastic waste
        self.history_service.create_record({
            "timestamp": "2026-06-23T16:00:00",
            "activities": [
                {"name": "Plastic Waste Bags", "category": "waste", "quantity": 10.0, "unit": "kg", "factor": 0.5, "carbon": 5.0}
            ]
        })
        
        analysis = self.coach_service.get_analysis()
        self.assertEqual(analysis.waste.waste_profile, "high_plastic_generation")

    def test_recommendation_generation(self):
        # High transport profile ratio trigger
        self.history_service.create_record({
            "timestamp": "2026-06-23T10:00:00",
            "activities": [
                {"name": "Petrol Car", "category": "transport", "quantity": 100.0, "unit": "km", "factor": 0.2, "carbon": 20.0}
            ]
        })
        from app.coach.recommendation_engine import generate_recommendations
        recs = generate_recommendations(self.history_service.get_all())
        self.assertTrue("Increase train or bus usage" in recs)

    def test_weekly_report(self):
        # Log active items in current week
        self.history_service.create_record({
            "timestamp": datetime.utcnow().isoformat(),
            "activities": [
                {"name": "Chicken Biriyani", "category": "food", "quantity": 1.0, "unit": "portions", "factor": 2.5, "carbon": 2.5}
            ]
        })
        report = self.coach_service.get_weekly_report()
        self.assertEqual(report.weekly_carbon, 2.5)
        self.assertEqual(report.top_source, "Chicken Biriyani")
        self.assertTrue(report.potential_reduction > 0)

    def test_monthly_report(self):
        # Log active items in current month
        self.history_service.create_record({
            "timestamp": datetime.utcnow().isoformat(),
            "activities": [
                {"name": "AC 1500W", "category": "energy", "quantity": 2.0, "unit": "hours", "factor": 1.2, "carbon": 2.4}
            ]
        })
        report = self.coach_service.get_monthly_report()
        self.assertEqual(report.monthly_carbon, 2.4)
        self.assertTrue(len(report.category_ranking) > 0)

    def test_achievement_detection(self):
        # Log low carbon day (< 1.0 kg)
        self.history_service.create_record({
            "timestamp": datetime.utcnow().isoformat(),
            "activities": [
                {"name": "Electric Train", "category": "transport", "quantity": 10.0, "unit": "km", "factor": 0.02, "carbon": 0.2}
            ]
        })
        report = self.coach_service.get_monthly_report()
        self.assertTrue("low_carbon_day" in report.achievements)

    def test_coach_queries(self):
        self.history_service.create_record({
            "timestamp": datetime.utcnow().isoformat(),
            "activities": [
                {"name": "Chicken Biriyani", "category": "food", "quantity": 1.0, "unit": "portion", "factor": 2.5, "carbon": 2.5}
            ]
        })
        
        ans_source = self.coach_service.answer_chat_query("What is my biggest source?")
        self.assertTrue("Chicken Biriyani" in ans_source)
        
        ans_plan = self.coach_service.answer_chat_query("Provide a 7-day sustainability plan")
        self.assertTrue("Day 1" in ans_plan)

    def test_performance(self):
        # Populate history with multiple records
        for i in range(10):
            self.history_service.create_record({
                "timestamp": (datetime.utcnow() - timedelta(days=i)).isoformat(),
                "activities": [
                    {"name": "AC 1500W", "category": "energy", "quantity": 2.0, "unit": "hours", "factor": 1.2, "carbon": 2.4},
                    {"name": "Petrol Car", "category": "transport", "quantity": 15.0, "unit": "km", "factor": 0.2, "carbon": 3.0}
                ]
            })
            
        # Analysis < 500ms
        start = time.perf_counter()
        self.coach_service.get_analysis()
        dur_analysis = (time.perf_counter() - start) * 1000
        self.assertLess(dur_analysis, 500.0)
        
        # Weekly < 1000ms
        start = time.perf_counter()
        self.coach_service.get_weekly_report()
        dur_weekly = (time.perf_counter() - start) * 1000
        self.assertLess(dur_weekly, 1000.0)
        
        # Monthly < 1000ms
        start = time.perf_counter()
        self.coach_service.get_monthly_report()
        dur_monthly = (time.perf_counter() - start) * 1000
        self.assertLess(dur_monthly, 1000.0)

    def test_new_user_scenarios(self):
        # Scenario 1: Empty history
        analysis = self.coach_service.get_analysis()
        self.assertEqual(analysis.energy.finding, "")
        self.assertEqual(analysis.food.finding, "")
        self.assertEqual(analysis.transport.finding, "")
        self.assertEqual(analysis.waste.finding, "")
        self.assertEqual(analysis.patterns, [])

        # Scenario 2: One activity (e.g. food only)
        self.setUp() # reset repo
        self.history_service.create_record({
            "timestamp": datetime.utcnow().isoformat(),
            "activities": [
                {"name": "Chicken Biriyani", "category": "food", "quantity": 1.0, "unit": "portions", "factor": 2.5, "carbon": 2.5}
            ]
        })
        analysis = self.coach_service.get_analysis()
        self.assertNotEqual(analysis.food.finding, "")
        self.assertEqual(analysis.energy.finding, "")
        self.assertEqual(analysis.transport.finding, "")
        self.assertEqual(analysis.waste.finding, "")

        # Scenario 3: Two activities (e.g. food and transport)
        self.setUp() # reset repo
        self.history_service.create_record({
            "timestamp": datetime.utcnow().isoformat(),
            "activities": [
                {"name": "Chicken Biriyani", "category": "food", "quantity": 1.0, "unit": "portions", "factor": 2.5, "carbon": 2.5},
                {"name": "Petrol Car", "category": "transport", "quantity": 10.0, "unit": "km", "factor": 0.2, "carbon": 2.0}
            ]
        })
        analysis = self.coach_service.get_analysis()
        self.assertNotEqual(analysis.food.finding, "")
        self.assertNotEqual(analysis.transport.finding, "")
        self.assertEqual(analysis.energy.finding, "")
        self.assertEqual(analysis.waste.finding, "")

        # Scenario 4: Missing category data (e.g. waste is missing)
        self.setUp() # reset repo
        self.history_service.create_record({
            "timestamp": datetime.utcnow().isoformat(),
            "activities": [
                {"name": "AC 1500W", "category": "energy", "quantity": 2.0, "unit": "hours", "factor": 1.2, "carbon": 2.4},
                {"name": "Chicken Biriyani", "category": "food", "quantity": 1.0, "unit": "portions", "factor": 2.5, "carbon": 2.5},
                {"name": "Petrol Car", "category": "transport", "quantity": 10.0, "unit": "km", "factor": 0.2, "carbon": 2.0}
            ]
        })
        analysis = self.coach_service.get_analysis()
        self.assertNotEqual(analysis.energy.finding, "")
        self.assertNotEqual(analysis.food.finding, "")
        self.assertNotEqual(analysis.transport.finding, "")
        self.assertEqual(analysis.waste.finding, "")

if __name__ == "__main__":
    unittest.main()
