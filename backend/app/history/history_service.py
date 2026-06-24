import csv
import io
import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.history.history_repository import HistoryRepository
from app.history.history_models import (
    ActivityHistoryItem,
    ActivityHistoryRecord,
    HistoryStatistics
)

class HistoryService:
    def __init__(self, repository: Optional[HistoryRepository] = None):
        self.repository = repository or HistoryRepository()

    def validate_record(self, record: dict) -> None:
        """
        Performs data validations (Module 11):
        - No duplicate records (handled at repository / UUID check)
        - No negative carbon values
        - No missing timestamps
        - No missing activity IDs
        - No corrupted entries
        """
        record_id = record.get("id")
        if not record_id or not isinstance(record_id, str) or len(record_id.strip()) == 0:
            raise ValueError("Record ID is missing or empty")

        timestamp = record.get("timestamp")
        if not timestamp or not isinstance(timestamp, str) or len(timestamp.strip()) == 0:
            raise ValueError("Timestamp is missing or empty")

        total_carbon = record.get("total_carbon", 0.0)
        if total_carbon < 0.0:
            raise ValueError("Total carbon cannot be negative")

        activities = record.get("activities", [])
        if not isinstance(activities, list):
            raise ValueError("Activities must be a list")

        for act in activities:
            name = act.get("name")
            category = act.get("category")
            quantity = act.get("quantity")
            unit = act.get("unit")
            factor = act.get("factor")
            carbon = act.get("carbon")

            # Check for corrupted entries
            if name is None or category is None or quantity is None or unit is None or factor is None or carbon is None:
                raise ValueError("Corrupted activity entry: missing required fields")

            if carbon < 0.0:
                raise ValueError("Activity carbon emission cannot be negative")

    def create_record(self, record_data: dict, db: Optional[Session] = None) -> dict:
        """
        Creates, validates, and persists a standard history record.
        """
        # Generate ID if missing
        if "id" not in record_data or not record_data["id"]:
            record_data["id"] = str(uuid.uuid4())

        # Check for duplicate ID in the repository
        existing = self.repository.get_by_id(record_data["id"], db=db)
        if existing:
            raise ValueError(f"Record with ID {record_data['id']} already exists")

        # Set default timestamp if missing
        if "timestamp" not in record_data or not record_data["timestamp"]:
            record_data["timestamp"] = datetime.utcnow().isoformat()

        activities = record_data.get("activities", [])
        
        # Calculate subtotals, categories, and total carbon emissions
        processed_activities = []
        total_carbon = 0.0
        categories_set = set()

        for act in activities:
            # Handle both Pydantic models and raw dicts
            act_dict = act if isinstance(act, dict) else act.dict()
            
            # Ensure carbon and subtotal are calculated if not present
            quantity = float(act_dict.get("quantity", 0.0))
            factor = float(act_dict.get("factor", 0.0))
            carbon = act_dict.get("carbon")
            
            if carbon is None:
                carbon = round(quantity * factor, 2)
            else:
                carbon = float(carbon)

            act_dict["carbon"] = carbon
            act_dict["subtotal"] = carbon
            
            # Ensure formula description is preserved or populated
            if "formula" not in act_dict or not act_dict["formula"]:
                act_dict["formula"] = f"{quantity} * {factor}"
                
            processed_activities.append(act_dict)
            total_carbon += carbon
            categories_set.add(act_dict.get("category", "other").lower())

        record_data["activities"] = processed_activities
        record_data["total_carbon"] = round(total_carbon, 2)
        record_data["categories"] = sorted(list(categories_set))
        
        if "source" not in record_data or not record_data["source"]:
            record_data["source"] = "manual"

        # Validate standard record before saving
        self.validate_record(record_data)

        # Save to repository
        return self.repository.save(record_data, db=db, user_id=user_id)

    def get_all(self, db: Optional[Session] = None, user_id: Optional[int] = None) -> List[dict]:
        return self.repository.get_all(db=db, user_id=user_id)

    def get_by_id(self, record_id: str, db: Optional[Session] = None, user_id: Optional[int] = None) -> Optional[dict]:
        return self.repository.get_by_id(record_id, db=db, user_id=user_id)

    def delete_record(self, record_id: str, db: Optional[Session] = None, user_id: Optional[int] = None) -> bool:
        return self.repository.delete(record_id, db=db, user_id=user_id)

    def update_record(self, record_id: str, updated_data: dict, db: Optional[Session] = None, user_id: Optional[int] = None) -> Optional[dict]:
        existing = self.repository.get_by_id(record_id, db=db, user_id=user_id)
        if not existing:
            return None

        # Recheck logic
        if "id" not in updated_data or not updated_data["id"]:
            updated_data["id"] = record_id
            
        if "timestamp" not in updated_data or not updated_data["timestamp"]:
            updated_data["timestamp"] = existing.get("timestamp")

        activities = updated_data.get("activities", [])
        processed_activities = []
        total_carbon = 0.0
        categories_set = set()

        for act in activities:
            act_dict = act if isinstance(act, dict) else act.dict()
            quantity = float(act_dict.get("quantity", 0.0))
            factor = float(act_dict.get("factor", 0.0))
            carbon = act_dict.get("carbon")
            
            if carbon is None:
                carbon = round(quantity * factor, 2)
            else:
                carbon = float(carbon)

            act_dict["carbon"] = carbon
            act_dict["subtotal"] = carbon
            if "formula" not in act_dict or not act_dict["formula"]:
                act_dict["formula"] = f"{quantity} * {factor}"
                
            processed_activities.append(act_dict)
            total_carbon += carbon
            categories_set.add(act_dict.get("category", "other").lower())

        updated_data["activities"] = processed_activities
        updated_data["total_carbon"] = round(total_carbon, 2)
        updated_data["categories"] = sorted(list(categories_set))
        
        if "source" not in updated_data:
            updated_data["source"] = existing.get("source", "manual")

        self.validate_record(updated_data)
        return self.repository.update(record_id, updated_data, db=db, user_id=user_id)

    def search_and_filter(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        carbon_level: Optional[str] = None, # "low", "high"
        sort_by: Optional[str] = "latest",
        db: Optional[Session] = None,
        user_id: Optional[int] = None
    ) -> List[dict]:
        """
        Executes Search (Module 6), Filtering (Module 5), and Sorting (Module 8).
        """
        records = self.repository.get_all(db=db, user_id=user_id)
        filtered = []

        for r in records:
            # 1. Date range filter
            timestamp_str = r.get("timestamp", "")
            if start_date:
                if timestamp_str < start_date:
                    continue
            if end_date:
                # Add check for inclusive end_date (e.g. if just date prefix like 2026-06-23)
                if timestamp_str > end_date and not timestamp_str.startswith(end_date):
                    continue

            # 2. Category filter
            if category:
                cats = [c.lower() for c in r.get("categories", [])]
                if category.lower() not in cats:
                    continue

            # 3. Carbon level filter
            # Low carbon: total_carbon <= 1.0
            # High carbon: total_carbon > 5.0
            total_carbon = r.get("total_carbon", 0.0)
            if carbon_level:
                if carbon_level.lower() == "low" and total_carbon > 1.0:
                    continue
                if carbon_level.lower() == "high" and total_carbon <= 5.0:
                    continue

            # 4. Search Query (matches Activity Name, Category, Date/Timestamp)
            if query:
                q = query.lower()
                matches_query = False
                
                # Check timestamp date string matches
                if q in timestamp_str.lower():
                    matches_query = True
                
                # Check categories
                for cat_item in r.get("categories", []):
                    if q in cat_item.lower():
                        matches_query = True
                        break
                        
                # Check individual activities
                for act in r.get("activities", []):
                    if q in act.get("name", "").lower() or q in act.get("category", "").lower():
                        matches_query = True
                        break
                
                if not matches_query:
                    continue

            filtered.append(r)

        # 5. Sorting (Module 8)
        if sort_by == "latest":
            filtered.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        elif sort_by == "oldest":
            filtered.sort(key=lambda x: x.get("timestamp", ""))
        elif sort_by == "highest_carbon":
            filtered.sort(key=lambda x: x.get("total_carbon", 0.0), reverse=True)
        elif sort_by == "lowest_carbon":
            filtered.sort(key=lambda x: x.get("total_carbon", 0.0))
        elif sort_by == "category":
            # Sort alphabetically by first category, fallback to empty string
            filtered.sort(key=lambda x: (x.get("categories", [""])[0] if x.get("categories") else ""))
        elif sort_by == "alphabetical":
            # Sort alphabetically by first activity's name
            filtered.sort(key=lambda x: (x.get("activities", [{}])[0].get("name", "") if x.get("activities") else ""))

        return filtered

    def generate_statistics(self, db: Optional[Session] = None, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Generates History Statistics (Module 10)
        """
        records = self.repository.get_all(db=db, user_id=user_id)
        if not records:
            return {
                "total_activities": 0,
                "total_carbon": 0.0,
                "average_carbon": 0.0,
                "most_frequent_activity": "N/A",
                "highest_carbon_activity": "N/A",
                "lowest_carbon_activity": "N/A"
            }

        total_activities = 0
        total_carbon = 0.0
        activity_counts = {}
        highest_carbon = -1.0
        highest_act_name = "N/A"
        lowest_carbon = float("inf")
        lowest_act_name = "N/A"

        for r in records:
            total_carbon += r.get("total_carbon", 0.0)
            activities = r.get("activities", [])
            total_activities += len(activities)
            
            for act in activities:
                name = act.get("name", "Unknown")
                activity_counts[name] = activity_counts.get(name, 0) + 1
                
                carbon = act.get("carbon", 0.0)
                if carbon > highest_carbon:
                    highest_carbon = carbon
                    highest_act_name = name
                if carbon < lowest_carbon:
                    lowest_carbon = carbon
                    lowest_act_name = name

        avg_carbon = round(total_carbon / len(records), 2)
        most_frequent = max(activity_counts, key=activity_counts.get) if activity_counts else "N/A"

        return {
            "total_activities": total_activities,
            "total_carbon": round(total_carbon, 2),
            "average_carbon": avg_carbon,
            "most_frequent_activity": most_frequent,
            "highest_carbon_activity": highest_act_name,
            "lowest_carbon_activity": lowest_act_name if lowest_carbon != float("inf") else "N/A"
        }

    def export_json(self, records: List[dict]) -> str:
        """
        Exports list of records to standard JSON format.
        """
        return json.dumps(records, indent=2, ensure_ascii=False)

    def export_csv(self, records: List[dict]) -> str:
        """
        Exports list of records to CSV format.
        Preserves all entities, factors, formulas, and subtotals.
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write Header
        writer.writerow([
            "record_id", "timestamp", "total_carbon", "source",
            "activity_name", "category", "quantity", "unit", "factor", "carbon_subtotal"
        ])
        
        for r in records:
            rec_id = r.get("id")
            ts = r.get("timestamp")
            tot = r.get("total_carbon")
            src = r.get("source")
            
            activities = r.get("activities", [])
            if not activities:
                # Still output record info even if empty
                writer.writerow([rec_id, ts, tot, src, "", "", "", "", "", ""])
            else:
                for act in activities:
                    writer.writerow([
                        rec_id, ts, tot, src,
                        act.get("name", ""),
                        act.get("category", ""),
                        act.get("quantity", ""),
                        act.get("unit", ""),
                        act.get("factor", ""),
                        act.get("carbon", "")
                    ])
                    
        return output.getvalue()
