import json
import os
import threading
from typing import List, Dict, Any

class GamificationRepository:
    def __init__(self, file_path: str = None):
        if file_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(base_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            file_path = os.path.join(data_dir, "gamification.json")
        self.file_path = file_path
        self.lock = threading.Lock()
        
        if not os.path.exists(self.file_path):
            self._write_data_internal({})
            
    def _read_data_internal(self) -> Dict[str, Any]:
        try:
            if not os.path.exists(self.file_path):
                return {}
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except Exception:
            return {}
            
    def _write_data_internal(self, data: Dict[str, Any]):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
    def get_redeemed_rewards(self, username: str) -> List[str]:
        with self.lock:
            data = self._read_data_internal()
            user_data = data.get(username, {})
            return user_data.get("redeemed_rewards", [])
            
    def redeem_reward(self, username: str, reward_id: str) -> List[str]:
        with self.lock:
            data = self._read_data_internal()
            if username not in data:
                data[username] = {"redeemed_rewards": []}
            redeemed = data[username].get("redeemed_rewards", [])
            if reward_id not in redeemed:
                redeemed.append(reward_id)
            data[username]["redeemed_rewards"] = redeemed
            self._write_data_internal(data)
            return redeemed

    def clear(self):
        with self.lock:
            self._write_data_internal({})
