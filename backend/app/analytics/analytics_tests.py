import unittest
import time
from datetime import datetime, date, timedelta
from app.analytics.daily_summary import calculate_daily_summary
from app.analytics.weekly_summary import calculate_weekly_summary
from app.analytics.monthly_summary import calculate_monthly_summary
from app.analytics.category_breakdown import calculate_category_breakdown
from app.analytics.emission_ranking import calculate_emission_ranking
from app.analytics.sustainability_score import calculate_sustainability_score
from app.analytics.recommendation_engine import generate_recommendations
from app.analytics.analytics_service import generate_analytics_payload

class TestAnalyticsEngine(unittest.TestCase):
    def setUp(self):
        self.ref_date = date(2026, 6, 22)
        
        # Helper dates
        self.today_dt = datetime(2026, 6, 22, 12, 0, 0)
        self.yesterday_dt = datetime(2026, 6, 21, 12, 0, 0)
        self.days_3_ago_dt = datetime(2026, 6, 19, 12, 0, 0)
        self.days_10_ago_dt = datetime(2026, 6, 12, 12, 0, 0)
        self.days_40_ago_dt = datetime(2026, 5, 13, 12, 0, 0)

        # Sample activities as dictionaries
        self.activities = [
            # Today
            {"item": "Car ride", "category": "transport", "calculated_value": 4.5, "logged_at": self.today_dt.isoformat()},
            {"item": "Steak dinner", "category": "food", "calculated_value": 6.2, "logged_at": self.today_dt.isoformat()},
            # Yesterday
            {"item": "Bus trip", "category": "transport", "calculated_value": 1.2, "logged_at": self.yesterday_dt.isoformat()},
            # 3 days ago
            {"item": "AC unit run", "category": "electricity", "calculated_value": 8.0, "logged_at": self.days_3_ago_dt.isoformat()},
            # 10 days ago
            {"item": "Food scraps", "category": "waste", "calculated_value": 0.5, "logged_at": self.days_10_ago_dt.isoformat()},
            # 40 days ago (outside 30d monthly range but inside 60d trend range)
            {"item": "Flight", "category": "transport", "calculated_value": 50.0, "logged_at": self.days_40_ago_dt.isoformat()},
            # Carbon-reducing walk
            {"item": "Walk to office", "category": "transport", "calculated_value": 0.0, "logged_at": self.today_dt.isoformat()},
        ]

    def test_daily_summary(self):
        summary = calculate_daily_summary(self.activities, self.ref_date)
        self.assertEqual(summary["activities"], 3)
        # 4.5 (Car ride) + 6.2 (Steak dinner) + 0.0 (Walk) = 10.7
        self.assertAlmostEqual(summary["total_carbon"], 10.7)
        self.assertEqual(summary["highest_activity"], "Steak dinner")
        self.assertAlmostEqual(summary["highest_carbon"], 6.2)

    def test_weekly_summary(self):
        summary = calculate_weekly_summary(self.activities, self.ref_date)
        # Weekly sums: today (10.7) + yesterday (1.2) + 3 days ago (8.0) = 19.9
        self.assertAlmostEqual(summary["weekly_total"], 19.9)
        self.assertAlmostEqual(summary["daily_average"], round(19.9 / 7, 2))
        self.assertEqual(summary["highest_day"], "Monday") # June 22, 2026 is Monday

    def test_monthly_summary(self):
        summary = calculate_monthly_summary(self.activities, self.ref_date)
        # Monthly sums: 10.7 + 1.2 + 8.0 + 0.5 = 20.4 (40 days ago flight is excluded)
        self.assertAlmostEqual(summary["monthly_total"], 20.4)
        self.assertAlmostEqual(summary["daily_average"], round(20.4 / 30, 2))

    def test_category_breakdown_100_percent(self):
        breakdown = calculate_category_breakdown(self.activities)
        total_pct = sum(breakdown.values())
        self.assertEqual(total_pct, 100)
        self.assertIn("transport", breakdown)
        self.assertIn("food", breakdown)
        self.assertIn("energy", breakdown)
        self.assertIn("waste", breakdown)

    def test_category_breakdown_empty(self):
        breakdown = calculate_category_breakdown([])
        self.assertEqual(breakdown["transport"], 0)
        self.assertEqual(breakdown["food"], 0)
        self.assertEqual(breakdown["energy"], 0)
        self.assertEqual(breakdown["waste"], 0)

    def test_sustainability_score_and_grade(self):
        # High emissions
        score_high = calculate_sustainability_score(self.activities, daily_average=10.0, category_breakdown={"transport": 50, "food": 20, "energy": 20, "waste": 10})
        self.assertLess(score_high["score"], 100)
        # Grades mapping check
        self.assertIn(score_high["grade"], ["A+", "A", "B", "C", "D"])
        
        # Perfect sustainability score
        perfect_activities = [{"item": "Walking", "category": "transport", "calculated_value": 0.0, "logged_at": self.today_dt.isoformat()}]
        score_low = calculate_sustainability_score(perfect_activities, daily_average=0.1, category_breakdown={"transport": 0, "food": 0, "energy": 0, "waste": 0})
        self.assertEqual(score_low["score"], 100)
        self.assertEqual(score_low["grade"], "A+")

    def test_recommendation_triggers(self):
        recs = generate_recommendations({"transport": 45, "food": 10, "energy": 10, "waste": 10})
        self.assertIn("Use public transport more often.", recs)
        
        recs_balanced = generate_recommendations({"transport": 10, "food": 10, "energy": 10, "waste": 10})
        self.assertTrue(len(recs_balanced) >= 2)
        self.assertIn("Consider walking or cycling for short-distance trips.", recs_balanced)

    def test_analytics_payload_and_trends(self):
        payload = generate_analytics_payload(self.activities, self.ref_date)
        self.assertIn("daily", payload)
        self.assertIn("weekly", payload)
        self.assertIn("monthly", payload)
        self.assertIn("category_breakdown", payload)
        self.assertIn("sustainability", payload)
        self.assertIn("recommendations", payload)
        
        # Trends
        self.assertIn("trend_status", payload["daily"])
        self.assertIn("trend_value", payload["daily"])
        self.assertIn("trend_status", payload["weekly"])
        self.assertIn("trend_status", payload["monthly"])

    def test_performance_under_500ms(self):
        # Generate 1000 items to check execution speed
        large_activities = []
        for i in range(1000):
            large_activities.append({
                "item": f"Item {i}",
                "category": "transport" if i % 2 == 0 else "food",
                "calculated_value": 1.5,
                "logged_at": (self.today_dt - timedelta(days=i%60)).isoformat()
            })
        
        start_time = time.perf_counter()
        generate_analytics_payload(large_activities, self.ref_date)
        end_time = time.perf_counter()
        
        execution_time_ms = (end_time - start_time) * 1000
        print(f"Execution time for 1000 activities: {execution_time_ms:.2f}ms")
        self.assertLess(execution_time_ms, 500.0)

if __name__ == "__main__":
    unittest.main()
