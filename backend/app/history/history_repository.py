import json
import os
import threading
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

class HistoryRepository:
    def __init__(self, db: Optional[Session] = None, file_path: str = None):
        self.db = db
        self.file_path = file_path
        self.lock = threading.Lock()
        
        # Initialize file if in file mode and file does not exist
        if self.file_path is not None:
            if not os.path.exists(self.file_path):
                self._write_data_internal([])
            
    def _read_data_internal(self) -> List[dict]:
        if self.file_path is None:
            return []
        try:
            if not os.path.exists(self.file_path):
                return []
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except Exception:
            return []
            
    def _write_data_internal(self, data: List[dict]):
        if self.file_path is None:
            return
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
    def get_all(self, db: Optional[Session] = None, user_id: Optional[int] = None) -> List[dict]:
        active_db = db or self.db
        if active_db is not None:
            # PostgreSQL mode
            from app.models.history import History
            from app.models.models import Activity
            # Query History filtered by user_id if provided
            query = active_db.query(History)
            if user_id is not None:
                query = query.filter(History.user_id == user_id)
            history_entries = query.order_by(History.created_at.desc()).all()
            records = []
            for h in history_entries:
                act = h.activity
                if not act:
                    continue
                # Map act and entities
                entities_list = []
                for ent in act.entities:
                    formula = None
                    if isinstance(act.metadata_json, dict):
                        formula = act.metadata_json.get("formula")
                    if not formula:
                        formula = f"{ent.quantity} * {ent.factor}"
                    entities_list.append({
                        "name": ent.entity_name,
                        "category": ent.entity_category,
                        "quantity": ent.quantity,
                        "unit": ent.unit,
                        "factor": ent.factor,
                        "carbon": ent.carbon_emission,
                        "subtotal": ent.carbon_emission,
                        "formula": formula
                    })
                categories = sorted(list(set(ent.entity_category.lower() for ent in act.entities)))
                records.append({
                    "id": str(h.id),
                    "timestamp": act.logged_at.isoformat() if act.logged_at else h.created_at.isoformat(),
                    "activities": entities_list,
                    "categories": categories,
                    "total_carbon": act.calculated_value,
                    "source": act.metadata_json.get("source", "manual") if isinstance(act.metadata_json, dict) else "manual"
                })
            return records
        else:
            # File mode
            with self.lock:
                return self._read_data_internal()
        
    def get_by_id(self, record_id: str, db: Optional[Session] = None, user_id: Optional[int] = None) -> Optional[dict]:
        active_db = db or self.db
        if active_db is not None:
            try:
                hist_id = int(record_id)
            except ValueError:
                return None
            from app.models.history import History
            query = active_db.query(History).filter(History.id == hist_id)
            if user_id is not None:
                query = query.filter(History.user_id == user_id)
            h = query.first()
            if not h or not h.activity:
                return None
            act = h.activity
            entities_list = []
            for ent in act.entities:
                formula = None
                if isinstance(act.metadata_json, dict):
                    formula = act.metadata_json.get("formula")
                if not formula:
                    formula = f"{ent.quantity} * {ent.factor}"
                entities_list.append({
                    "name": ent.entity_name,
                    "category": ent.entity_category,
                    "quantity": ent.quantity,
                    "unit": ent.unit,
                    "factor": ent.factor,
                    "carbon": ent.carbon_emission,
                    "subtotal": ent.carbon_emission,
                    "formula": formula
                })
            categories = sorted(list(set(ent.entity_category.lower() for ent in act.entities)))
            return {
                "id": str(h.id),
                "timestamp": act.logged_at.isoformat() if act.logged_at else h.created_at.isoformat(),
                "activities": entities_list,
                "categories": categories,
                "total_carbon": act.calculated_value,
                "source": act.metadata_json.get("source", "manual") if isinstance(act.metadata_json, dict) else "manual"
            }
        else:
            with self.lock:
                data = self._read_data_internal()
                for r in data:
                    if r.get("id") == record_id:
                        return r
                return None
        
    def save(self, record: dict, db: Optional[Session] = None, user_id: Optional[int] = None) -> dict:
        active_db = db or self.db
        if active_db is not None:
            # Save to PostgreSQL
            from app.models.models import User, Activity
            from app.models.activity_entity import ActivityEntity
            from app.models.history import History
            from datetime import datetime
            
            # Find user
            if user_id is not None:
                user = active_db.query(User).filter(User.id == user_id).first()
            else:
                user = active_db.query(User).filter(User.username == "demo_user").first()
            
            if not user:
                user_username = "demo_user" if user_id is None else f"user_{user_id}"
                user = User(username=user_username, xp=0, level=1)
                active_db.add(user)
                active_db.commit()
                active_db.refresh(user)
            
            # Parse timestamp
            ts_str = record.get("timestamp")
            if ts_str:
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", ""))
                except Exception:
                    ts = datetime.utcnow()
            else:
                ts = datetime.utcnow()
                
            # Create Activity row
            activities_in_record = record.get("activities", [])
            primary_act_name = activities_in_record[0].get("name") if activities_in_record else "activity"
            primary_category = activities_in_record[0].get("category") if activities_in_record else "lifestyle"
            primary_quantity = activities_in_record[0].get("quantity") if activities_in_record else 1.0
            primary_unit = activities_in_record[0].get("unit") if activities_in_record else "unit"
            
            act = Activity(
                user_id=user.id,
                input_text=primary_act_name,
                category=primary_category,
                item=primary_act_name,
                quantity=primary_quantity,
                unit=primary_unit,
                calculated_value=record.get("total_carbon", 0.0),
                metadata_json={"source": record.get("source", "manual")},
                region="Global",
                logged_at=ts
            )
            active_db.add(act)
            active_db.commit()
            active_db.refresh(act)
            
            # Create ActivityEntity rows
            for item in activities_in_record:
                formula = item.get("formula") or f"{item.get('quantity')} * {item.get('factor')}"
                ent = ActivityEntity(
                    activity_id=act.id,
                    entity_name=item.get("name"),
                    entity_category=item.get("category"),
                    quantity=item.get("quantity"),
                    unit=item.get("unit"),
                    factor=item.get("factor"),
                    carbon_emission=item.get("carbon")
                )
                active_db.add(ent)
            active_db.commit()
            
            # Create History row
            h = History(
                user_id=user.id,
                activity_id=act.id,
                created_at=ts
            )
            active_db.add(h)
            active_db.commit()
            active_db.refresh(h)
            
            # Return identical dictionary
            record["id"] = str(h.id)
            record["timestamp"] = act.logged_at.isoformat()
            
            # Fill default values
            for i, act_item in enumerate(record.get("activities", [])):
                act_item["subtotal"] = act_item.get("carbon")
                if "formula" not in act_item:
                    act_item["formula"] = f"{act_item.get('quantity')} * {act_item.get('factor')}"
                    
            categories = sorted(list(set(item.get("category").lower() for item in record.get("activities", []))))
            record["categories"] = categories
            return record
        else:
            with self.lock:
                data = self._read_data_internal()
                data = [r for r in data if r.get("id") != record.get("id")]
                data.append(record)
                self._write_data_internal(data)
                return record
        
    def delete(self, record_id: str, db: Optional[Session] = None, user_id: Optional[int] = None) -> bool:
        active_db = db or self.db
        if active_db is not None:
            try:
                hist_id = int(record_id)
            except ValueError:
                return False
            from app.models.history import History
            h = active_db.query(History).filter(History.id == hist_id).first()
            if not h:
                return False
            if user_id is not None and h.user_id != user_id:
                return False
            act = h.activity
            active_db.delete(h)
            if act:
                active_db.delete(act)
            active_db.commit()
            return True
        else:
            with self.lock:
                data = self._read_data_internal()
                initial_len = len(data)
                data = [r for r in data if r.get("id") != record_id]
                if len(data) < initial_len:
                    self._write_data_internal(data)
                    return True
                return False
        
    def update(self, record_id: str, updated_data: dict, db: Optional[Session] = None, user_id: Optional[int] = None) -> Optional[dict]:
        active_db = db or self.db
        if active_db is not None:
            try:
                hist_id = int(record_id)
            except ValueError:
                return None
            from app.models.history import History
            h = active_db.query(History).filter(History.id == hist_id).first()
            if not h:
                return None
            if user_id is not None and h.user_id != user_id:
                return None
            act = h.activity
            if not act:
                return None
            
            # Update Activity values
            act.calculated_value = updated_data.get("total_carbon", 0.0)
            if updated_data.get("timestamp"):
                from datetime import datetime
                try:
                    act.logged_at = datetime.fromisoformat(updated_data.get("timestamp").replace("Z", ""))
                    h.created_at = act.logged_at
                except Exception:
                    pass
            
            # Recreate ActivityEntity rows (delete existing first)
            for ent in act.entities:
                active_db.delete(ent)
            active_db.commit()
            
            from app.models.activity_entity import ActivityEntity
            for item in updated_data.get("activities", []):
                ent = ActivityEntity(
                    activity_id=act.id,
                    entity_name=item.get("name"),
                    entity_category=item.get("category"),
                    quantity=item.get("quantity"),
                    unit=item.get("unit"),
                    factor=item.get("factor"),
                    carbon_emission=item.get("carbon")
                )
                active_db.add(ent)
            active_db.commit()
            
            updated_data["id"] = record_id
            return updated_data
        else:
            with self.lock:
                data = self._read_data_internal()
                for i, r in enumerate(data):
                    if r.get("id") == record_id:
                        updated_data["id"] = record_id
                        data[i] = updated_data
                        self._write_data_internal(data)
                        return updated_data
                return None

    def clear(self, db: Optional[Session] = None, user_id: Optional[int] = None):
        active_db = db or self.db
        if active_db is not None:
            from app.models.history import History
            from app.models.models import Activity
            # Clear all or only user's records
            if user_id is not None:
                # Delete activities cascade deletes history entries linked to them
                history_query = active_db.query(History).filter(History.user_id == user_id)
                for h in history_query.all():
                    act = h.activity
                    active_db.delete(h)
                    if act:
                        active_db.delete(act)
            else:
                active_db.query(History).delete()
                active_db.query(Activity).delete()
            active_db.commit()
        else:
            with self.lock:
                self._write_data_internal([])
