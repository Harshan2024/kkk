import json
import os
import threading
from typing import List, Optional

class HistoryRepository:
    def __init__(self, file_path: str = None):
        if file_path is None:
            # Place in the local data directory
            base_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(base_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            file_path = os.path.join(data_dir, "history.json")
        self.file_path = file_path
        self.lock = threading.Lock()
        
        # Initialize file if it does not exist
        if not os.path.exists(self.file_path):
            self._write_data_internal([])
            
    def _read_data_internal(self) -> List[dict]:
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
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
    def get_all(self) -> List[dict]:
        with self.lock:
            return self._read_data_internal()
        
    def get_by_id(self, record_id: str) -> Optional[dict]:
        with self.lock:
            data = self._read_data_internal()
            for r in data:
                if r.get("id") == record_id:
                    return r
            return None
        
    def save(self, record: dict) -> dict:
        with self.lock:
            data = self._read_data_internal()
            # De-duplicate by ID
            data = [r for r in data if r.get("id") != record.get("id")]
            data.append(record)
            self._write_data_internal(data)
            return record
        
    def delete(self, record_id: str) -> bool:
        with self.lock:
            data = self._read_data_internal()
            initial_len = len(data)
            data = [r for r in data if r.get("id") != record_id]
            if len(data) < initial_len:
                self._write_data_internal(data)
                return True
            return False
        
    def update(self, record_id: str, updated_data: dict) -> Optional[dict]:
        with self.lock:
            data = self._read_data_internal()
            for i, r in enumerate(data):
                if r.get("id") == record_id:
                    updated_data["id"] = record_id
                    data[i] = updated_data
                    self._write_data_internal(data)
                    return updated_data
            return None

    def clear(self):
        with self.lock:
            self._write_data_internal([])
