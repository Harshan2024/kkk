from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ChallengeProgress(BaseModel):
    id: str
    name: str
    description: str
    xp: int
    progress: float
    max: float
    completed: bool
    icon: str
    color: str

class AchievementStatus(BaseModel):
    id: str
    name: str
    description: str
    badge_type: str
    unlocked: bool
    unlocked_at: Optional[str] = None
    progress: float

class VirtualReward(BaseModel):
    id: str
    name: str
    description: str
    cost: int
    redeemed: bool
    icon: str

class GamificationProfile(BaseModel):
    username: str
    xp: int
    level: int
    streak: int
    sustainability_score: float
    available_xp: int
    total_xp: int
    xp_needed_for_next_level: int
    xp_in_current_level: int
    level_progress_pct: float
    redeemed_rewards: List[str]

class RedeemRequest(BaseModel):
    reward_id: str
    username: Optional[str] = "demo_user"
