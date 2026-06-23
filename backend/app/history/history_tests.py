import unittest
import os
import json
import time
from datetime import datetime, timedelta
from app.history.history_repository import HistoryRepository
from app.history.history_service import HistoryService

class TestHistorySystem(unittest.TestCase):
    def setUp(self):
        self.test_file = "test_history.json"
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
            
        self.repo = HistoryRepository(file_path=self.test_file)
        self.service = HistoryService(repository=self.repo)

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_single_entity_save(self):
        record_data = {
            "timestamp": "2026-06-23T10:15:00",
            "activities": [
                {
                    "name": "Electric Train",
                    "category": "transport",
                    "quantity": 25.0,
                    "unit": "km",
                    "factor": 0.02,
                    "carbon": 0.50
                }
            ],
            "source": "manual"
        }
        record = self.service.create_record(record_data)
        self.assertIsNotNone(record["id"])
        self.assertEqual(record["total_carbon"], 0.50)
        self.assertEqual(record["categories"], ["transport"])
        self.assertEqual(len(record["activities"]), 1)
        self.assertEqual(record["activities"][0]["subtotal"], 0.50)

    def test_multi_entity_save(self):
        record_data = {
            "timestamp": "2026-06-23T12:00:00",
            "activities": [
                {
                    "name": "Electric Train",
                    "category": "transport",
                    "quantity": 25.0,
                    "unit": "km",
                    "factor": 0.02
                },
                {
                    "name": "Chicken Biriyani",
                    "category": "food",
                    "quantity": 2.0,
                    "unit": "portion",
                    "factor": 2.50
                },
                {
                    "name": "AC 1500W",
                    "category": "energy",
                    "quantity": 3.0,
                    "unit": "hours",
                    "factor": 1.23
                }
            ]
        }
        record = self.service.create_record(record_data)
        # (25 * 0.02) + (2 * 2.50) + (3 * 1.23) = 0.5 + 5.0 + 3.69 = 9.19
        self.assertEqual(record["total_carbon"], 9.19)
        self.assertEqual(record["categories"], ["energy", "food", "transport"])
        self.assertEqual(len(record["activities"]), 3)
        self.assertTrue("25" in record["activities"][0]["formula"])

    def test_validation_errors(self):
        # Negative carbon
        record_data = {
            "activities": [
                {
                    "name": "Electric Train",
                    "category": "transport",
                    "quantity": 25.0,
                    "unit": "km",
                    "factor": 0.02,
                    "carbon": -0.50
                }
            ]
        }
        with self.assertRaises(ValueError):
            self.service.create_record(record_data)

        # Missing name (corrupted)
        record_data_corrupt = {
            "activities": [
                {
                    "category": "transport",
                    "quantity": 25.0,
                    "unit": "km",
                    "factor": 0.02
                }
            ]
        }
        with self.assertRaises(ValueError):
            self.service.create_record(record_data_corrupt)

    def test_search_and_filter(self):
        r1 = self.service.create_record({
            "timestamp": "2026-06-20T10:00:00",
            "activities": [{"name": "Chicken Biriyani", "category": "food", "quantity": 1, "unit": "portion", "factor": 2.5}]
        })
        r2 = self.service.create_record({
            "timestamp": "2026-06-21T10:00:00",
            "activities": [{"name": "Electric Train", "category": "transport", "quantity": 10, "unit": "km", "factor": 0.02}]
        })
        r3 = self.service.create_record({
            "timestamp": "2026-06-22T10:00:00",
            "activities": [{"name": "Plastic Waste", "category": "waste", "quantity": 50, "unit": "kg", "factor": 0.1}]
        })

        # Search
        results = self.service.search_and_filter(query="Train")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], r2["id"])

        # Filter Category
        results = self.service.search_and_filter(category="food")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], r1["id"])

        # Filter Carbon Level (Low carbon <= 1.0)
        results = self.service.search_and_filter(carbon_level="low")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], r2["id"])

    def test_sorting(self):
        r1 = self.service.create_record({
            "timestamp": "2026-06-20T10:00:00",
            "activities": [{"name": "Chicken Biriyani", "category": "food", "quantity": 1, "unit": "portion", "factor": 2.5}]
        })
        r2 = self.service.create_record({
            "timestamp": "2026-06-21T10:00:00",
            "activities": [{"name": "Electric Train", "category": "transport", "quantity": 10, "unit": "km", "factor": 0.02}]
        })

        # Latest
        results = self.service.search_and_filter(sort_by="latest")
        self.assertEqual(results[0]["id"], r2["id"])

        # Highest Carbon
        results = self.service.search_and_filter(sort_by="highest_carbon")
        self.assertEqual(results[0]["id"], r1["id"])

    def test_export(self):
        self.service.create_record({
            "timestamp": "2026-06-20T10:00:00",
            "activities": [{"name": "Chicken Biriyani", "category": "food", "quantity": 1, "unit": "portion", "factor": 2.5}]
        })
        records = self.service.get_all()
        
        json_export = self.service.export_json(records)
        self.assertTrue(len(json_export) > 0)
        json.loads(json_export)
        
        csv_export = self.service.export_csv(records)
        self.assertTrue("record_id" in csv_export)
        self.assertTrue("Chicken Biriyani" in csv_export)

    def test_statistics(self):
        self.service.create_record({
            "timestamp": "2026-06-20T10:00:00",
            "activities": [{"name": "Chicken Biriyani", "category": "food", "quantity": 1, "unit": "portion", "factor": 2.5}]
        })
        self.service.create_record({
            "timestamp": "2026-06-21T10:00:00",
            "activities": [{"name": "Electric Train", "category": "transport", "quantity": 10, "unit": "km", "factor": 0.02}]
        })
        
        stats = self.service.generate_statistics()
        self.assertEqual(stats["total_activities"], 2)
        self.assertEqual(stats["total_carbon"], 2.7)
        self.assertEqual(stats["highest_carbon_activity"], "Chicken Biriyani")

    def test_performance(self):
        record_data = {
            "activities": [{"name": "AC", "category": "energy", "quantity": 2, "unit": "hours", "factor": 0.5}]
        }
        
        # Save Record < 100ms
        start = time.perf_counter()
        self.service.create_record(record_data)
        dur_save = (time.perf_counter() - start) * 1000
        self.assertLess(dur_save, 100.0)
        
        # Load History < 200ms
        start = time.perf_counter()
        self.service.get_all()
        dur_load = (time.perf_counter() - start) * 1000
        self.assertLess(dur_load, 200.0)
        
        # Search < 100ms
        start = time.perf_counter()
        self.service.search_and_filter(query="AC")
        dur_search = (time.perf_counter() - start) * 1000
        self.assertLess(dur_search, 100.0)

if __name__ == "__main__":
    unittest.main()
