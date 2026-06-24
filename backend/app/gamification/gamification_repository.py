import json
import os
import threading
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

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
            
    def get_redeemed_rewards(self, username: str, db: Optional[Session] = None) -> List[str]:
        if db is not None:
            from app.models.models import User
            user = db.query(User).filter(User.username == username).first()
            if not user or not user.redeemed_rewards:
                return []
            return user.redeemed_rewards
        else:
            with self.lock:
                data = self._read_data_internal()
                user_data = data.get(username, {})
                return user_data.get("redeemed_rewards", [])
            
    def redeem_reward(self, username: str, reward_id: str, db: Optional[Session] = None) -> List[str]:
        if db is not None:
            from app.models.models import User
            user = db.query(User).filter(User.username == username).first()
            if not user:
                user = User(username=username, xp=0, level=1, redeemed_rewards=[])
                db.add(user)
                db.commit()
                db.refresh(user)
            
            redeemed = user.redeemed_rewards or []
            if reward_id not in redeemed:
                # Copy and update to trigger SQLAlchemy change detection on JSON field
                redeemed = list(redeemed) + [reward_id]
                user.redeemed_rewards = redeemed
                db.commit()
                db.refresh(user)
            return redeemed
        else:
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

    def clear(self, db: Optional[Session] = None):
        if db is not None:
            from app.models.models import User
            users = db.query(User).all()
            for u in users:
                u.redeemed_rewards = []
            db.commit()
        else:
            with self.lock:
                self._write_data_internal({})
