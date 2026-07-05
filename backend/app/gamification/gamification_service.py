from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.history.history_service import HistoryService
from app.gamification.gamification_models import (
    ChallengeProgress,
    AchievementStatus,
    VirtualReward,
    GamificationProfile
)
from app.gamification.gamification_repository import GamificationRepository

VIRTUAL_REWARDS_CATALOG = [
    {"id": "eco_avatar", "name": "Eco-Warrior Avatar Badge", "description": "Custom emerald avatar badge for your profile.", "cost": 100, "icon": "shield"},
    {"id": "solar_theme", "name": "Solar Panels Dashboard Theme", "description": "Vibrant solar orange and yellow visual theme.", "cost": 250, "icon": "palette"},
    {"id": "forest_title", "name": "Forest Protector Title", "description": "Custom title 'Forest Protector' displayed under your name.", "cost": 500, "icon": "award"},
    {"id": "climate_cert", "name": "Carbon Neutral Certificate", "description": "Digital downloadable carbon neutrality certificate.", "cost": 1000, "icon": "file"}
]

class GamificationService:
    def __init__(self, history_service: Optional[HistoryService] = None, repository: Optional[GamificationRepository] = None):
        self.history_service = history_service or HistoryService()
        self.repository = repository or GamificationRepository()

    def get_profile(self, username: str = "demo_user", db: Optional[Session] = None) -> GamificationProfile:
        user_id = None
        if db is not None:
            from app.models.models import User
            user = db.query(User).filter(User.username == username).first()
            if user:
                user_id = user.id
        records = self.history_service.get_all(db=db, user_id=user_id)
        
        # 1. Calculate base components
        streak = self.calculate_streak(records)
        sustainability_score = self.calculate_sustainability_score(records, streak)
        
        # 2. Calculate XP
        total_xp = self.calculate_total_xp(records, streak, username, db=db)
        
        # 3. Calculate Level metrics
        level = (total_xp // 300) + 1
        xp_in_current_level = total_xp % 300
        xp_needed_for_next_level = 300
        level_progress_pct = round((xp_in_current_level / 300.0) * 100, 2)
        
        # 4. Fetch redeemed rewards
        redeemed_rewards = self.repository.get_redeemed_rewards(username, db=db)
        
        # 5. Calculate available XP
        redeemed_cost = sum(
            r["cost"] for r in VIRTUAL_REWARDS_CATALOG if r["id"] in redeemed_rewards
        )
        available_xp = max(0, total_xp - redeemed_cost)
        
        return GamificationProfile(
            username=username,
            xp=total_xp,
            level=level,
            streak=streak,
            sustainability_score=sustainability_score,
            available_xp=available_xp,
            total_xp=total_xp,
            xp_needed_for_next_level=xp_needed_for_next_level,
            xp_in_current_level=xp_in_current_level,
            level_progress_pct=level_progress_pct,
            redeemed_rewards=redeemed_rewards
        )

    def get_achievements(self, username: str = "demo_user", db: Optional[Session] = None) -> List[AchievementStatus]:
        user_id = None
        if db is not None:
            from app.models.models import User
            user = db.query(User).filter(User.username == username).first()
            if user:
                user_id = user.id
        records = self.history_service.get_all(db=db, user_id=user_id)
        streak = self.calculate_streak(records)
        total_xp_pre_level5 = self.calculate_total_xp(records, streak, username, exclude_level5=True, db=db)
        level_pre_level5 = (total_xp_pre_level5 // 300) + 1
        
        # Compute category counters
        unique_dates = set()
        recycling_count = 0
        has_low_carbon = False
        
        for r in records:
            ts = r.get("timestamp")
            if ts:
                unique_dates.add(ts[:10])
            total_carbon = r.get("total_carbon", 0.0)
            if total_carbon > 0 and total_carbon < 1.0:
                has_low_carbon = True
            for act in r.get("activities", []):
                name = act.get("name", "").lower()
                category = act.get("category", "").lower()
                if category == "waste" and any(term in name for term in ["recycle", "recycling"]):
                    recycling_count += 1
                    
        total_days = len(unique_dates)
        
        achievements_def = [
            {
                "id": "first_log",
                "name": "First Steps",
                "description": "Log your first activity in CarbonTracker.",
                "badge_type": "bronze",
                "unlocked": total_days >= 1,
                "progress": 1.0 if total_days >= 1 else 0.0
            },
            {
                "id": "low_carbon_day",
                "name": "Carbon Minimalist",
                "description": "Log a day with daily emissions under 1.0 kg CO2e.",
                "badge_type": "bronze",
                "unlocked": has_low_carbon,
                "progress": 1.0 if has_low_carbon else 0.0
            },
            {
                "id": "streak_3",
                "name": "Dedicated Eco-Citizen",
                "description": "Achieve a 3-day consecutive logging streak.",
                "badge_type": "silver",
                "unlocked": streak >= 3,
                "progress": min(1.0, streak / 3.0)
            },
            {
                "id": "streak_7",
                "name": "Weekly Guardian",
                "description": "Achieve a 7-day consecutive logging streak.",
                "badge_type": "gold",
                "unlocked": streak >= 7,
                "progress": min(1.0, streak / 7.0)
            },
            {
                "id": "recycle_master",
                "name": "Zero Waste Champion",
                "description": "Log at least 3 waste recycling events.",
                "badge_type": "silver",
                "unlocked": recycling_count >= 3,
                "progress": min(1.0, recycling_count / 3.0)
            },
            {
                "id": "level_5",
                "name": "Sustainability Veteran",
                "description": "Reach Level 5 or higher.",
                "badge_type": "gold",
                "unlocked": level_pre_level5 >= 5,
                "progress": min(1.0, level_pre_level5 / 5.0)
            }
        ]
        
        results = []
        for ach in achievements_def:
            results.append(
                AchievementStatus(
                    id=ach["id"],
                    name=ach["name"],
                    description=ach["description"],
                    badge_type=ach["badge_type"],
                    unlocked=ach["unlocked"],
                    unlocked_at=datetime.utcnow().isoformat() if ach["unlocked"] else None,
                    progress=round(ach["progress"], 2)
                )
            )
        return results

    def get_challenges(self, username: str = "demo_user", db: Optional[Session] = None, records: Optional[List[Dict[str, Any]]] = None) -> Dict[str, List[ChallengeProgress]]:
        if records is None:
            user_id = None
            if db is not None:
                from app.models.models import User
                user = db.query(User).filter(User.username == username).first()
                if user:
                    user_id = user.id
            records = self.history_service.get_all(db=db, user_id=user_id)
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        week_ago = datetime.utcnow().date() - timedelta(days=7)
        
        # Today's records
        today_records = [r for r in records if r.get("timestamp", "").startswith(today_str)]
        # This week's records
        weekly_records = []
        for r in records:
            ts_str = r.get("timestamp", "")
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "")).date()
                if ts >= week_ago:
                    weekly_records.append(r)
            except ValueError:
                continue
                
        # --- 1. Daily Challenges ---
        # Challenge 1: Log a vegetarian food meal today
        has_veg_today = False
        for r in today_records:
            for act in r.get("activities", []):
                name = act.get("name", "").lower()
                category = act.get("category", "").lower()
                if category == "food":
                    is_animal = any(term in name for term in ["chicken", "mutton", "biriyani", "biryani", "briyani", "egg", "meat", "fish", "pork", "beef"])
                    if not is_animal:
                        has_veg_today = True
                        break
                        
        # Challenge 2: Keep AC runtime under 2 hours today
        has_energy_today = False
        ac_hours_today = 0.0
        for r in today_records:
            for act in r.get("activities", []):
                name = act.get("name", "").lower()
                category = act.get("category", "").lower()
                qty = float(act.get("quantity") or 0.0)
                if category in ["energy", "electricity", "appliances"]:
                    has_energy_today = True
                    if "ac" in name or "air conditioner" in name:
                        ac_hours_today += qty
                        
        ac_downtime_today = 0.0
        if has_energy_today and ac_hours_today < 2.0:
            ac_downtime_today = 1.0
            
        daily_challenges = [
            ChallengeProgress(
                id="daily_veg_meal",
                name="Go Green on Meals",
                description="Log a vegetarian or vegan food item today.",
                xp=50,
                progress=1.0 if has_veg_today else 0.0,
                max=1.0,
                completed=has_veg_today,
                icon="Leaf",
                color="text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
            ),
            ChallengeProgress(
                id="daily_ac_limit",
                name="AC Downtime",
                description="Keep AC runtime under 2 hours today.",
                xp=50,
                progress=ac_downtime_today,
                max=1.0,
                completed=ac_downtime_today == 1.0,
                icon="Plug",
                color="text-indigo-400 bg-indigo-500/10 border-indigo-500/20"
            )
        ]
        
        # --- 2. Weekly Challenges ---
        # Challenge 1: Log activities on 4 different days this week
        unique_weekly_days = set()
        for r in weekly_records:
            ts = r.get("timestamp")
            if ts:
                unique_weekly_days.add(ts[:10])
        log_athon_completed = len(unique_weekly_days) >= 4
        
        # Challenge 2: Commute at least 15 km via public transport this week
        public_commute_km = 0.0
        for r in weekly_records:
            for act in r.get("activities", []):
                name = act.get("name", "").lower()
                category = act.get("category", "").lower()
                qty = float(act.get("quantity") or 0.0)
                if category == "transport":
                    is_public = any(term in name for term in ["train", "bus", "metro", "subway", "tram", "public", "cycle", "cycling", "walk", "walking", "run", "running"])
                    if is_public:
                        public_commute_km += qty
                        
        public_champion_completed = public_commute_km >= 15.0
        
        weekly_challenges = [
            ChallengeProgress(
                id="weekly_log_athon",
                name="Log-a-Thon",
                description="Log activities on 4 different days this week.",
                xp=150,
                progress=float(min(4, len(unique_weekly_days))),
                max=4.0,
                completed=log_athon_completed,
                icon="Trophy",
                color="text-emerald-450 bg-emerald-500/10 border-emerald-500/20"
            ),
            ChallengeProgress(
                id="weekly_public_commute",
                name="Public Transit Champion",
                description="Commute at least 15 km via public transit this week.",
                xp=200,
                progress=round(min(15.0, public_commute_km), 1),
                max=15.0,
                completed=public_champion_completed,
                icon="Bike",
                color="text-sky-500 bg-sky-500/10 border-sky-500/20"
            )
        ]
        
        return {"daily": daily_challenges, "weekly": weekly_challenges}

    def get_rewards(self, username: str = "demo_user", db: Optional[Session] = None) -> List[VirtualReward]:
        redeemed = self.repository.get_redeemed_rewards(username, db=db)
        results = []
        for r in VIRTUAL_REWARDS_CATALOG:
            results.append(
                VirtualReward(
                    id=r["id"],
                    name=r["name"],
                    description=r["description"],
                    cost=r["cost"],
                    redeemed=r["id"] in redeemed,
                    icon=r["icon"]
                )
            )
        return results

    def redeem_reward(self, username: str, reward_id: str, db: Optional[Session] = None) -> Dict[str, Any]:
        catalog_item = next((r for r in VIRTUAL_REWARDS_CATALOG if r["id"] == reward_id), None)
        if not catalog_item:
            raise ValueError(f"Reward ID {reward_id} does not exist in catalog.")
            
        profile = self.get_profile(username, db=db)
        if reward_id in profile.redeemed_rewards:
            raise ValueError(f"Reward ID {reward_id} has already been redeemed.")
            
        if profile.available_xp < catalog_item["cost"]:
            raise ValueError(f"Insufficient XP. Cost is {catalog_item['cost']} XP, but you only have {profile.available_xp} XP available.")
            
        redeemed = self.repository.redeem_reward(username, reward_id, db=db)
        return {"status": "success", "message": f"Successfully redeemed {catalog_item['name']}", "redeemed_rewards": redeemed}

    # --- Engine Internal Calculators ---
    
    def calculate_streak(self, records: List[Dict[str, Any]]) -> int:
        if not records:
            return 0
            
        dates = sorted(list(set(r.get("timestamp", "")[:10] for r in records if r.get("timestamp"))))
        if not dates:
            return 0
            
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        
        last_logged_date = datetime.strptime(dates[-1], "%Y-%m-%d").date()
        if last_logged_date < yesterday:
            return 0
            
        streak = 1
        idx = len(dates) - 1
        while idx > 0:
            d1 = datetime.strptime(dates[idx], "%Y-%m-%d").date()
            d2 = datetime.strptime(dates[idx-1], "%Y-%m-%d").date()
            if (d1 - d2).days == 1:
                streak += 1
                idx -= 1
            elif (d1 - d2).days == 0:
                idx -= 1
            else:
                break
        return streak

    def calculate_sustainability_score(self, records: List[Dict[str, Any]], streak: int) -> float:
        """
        Calculates score between 10.0 and 100.0 based on emissions and logging consistency.
        """
        if not records:
            return 100.0
            
        # 1. Base score starts at 100
        score = 100.0
        
        # 2. Emissions Penalties
        transport_carbon = 0.0
        food_carbon = 0.0
        energy_carbon = 0.0
        
        for r in records:
            for act in r.get("activities", []):
                cat = act.get("category", "").lower()
                carbon = float(act.get("carbon") or 0.0)
                if cat == "transport":
                    transport_carbon += carbon
                elif cat == "food":
                    food_carbon += carbon
                elif cat in ["energy", "electricity", "appliances"]:
                    energy_carbon += carbon
                    
        # Apply subtractions for excessive emissions (normalized per record count)
        num_records = len(records)
        avg_transport = transport_carbon / num_records
        avg_food = food_carbon / num_records
        avg_energy = energy_carbon / num_records
        
        # Transport subtraction: 1 point per 3kg average emissions
        score -= (avg_transport / 3.0) * 5.0
        # Food subtraction: 1 point per 2kg average emissions
        score -= (avg_food / 2.0) * 4.0
        # Energy subtraction: 1 point per 4kg average emissions
        score -= (avg_energy / 4.0) * 5.0
        
        # 3. Consistency Bonuses
        # Active streak bonus: +2 points per streak day, max 20 points
        score += min(20.0, streak * 2.0)
        
        # Bound score between 10.0 and 100.0
        return round(max(10.0, min(100.0, score)), 1)

    def calculate_total_xp(self, records: List[Dict[str, Any]], streak: int, username: str, exclude_level5: bool = False, db: Optional[Session] = None) -> int:
        xp = 0
        
        # 1. XP from logging activities
        for r in records:
            # Base log reward: +20 XP per record
            xp += 20
            
            for act in r.get("activities", []):
                name = act.get("name", "").lower()
                category = act.get("category", "").lower()
                qty = float(act.get("quantity") or 0.0)
                
                # Category Specific Bonuses
                if category == "transport":
                    is_public = any(term in name for term in ["train", "bus", "metro", "subway", "tram", "public", "cycle", "cycling", "walk", "walking", "run", "running"])
                    xp += 30 if is_public else 10
                elif category == "food":
                    is_animal = any(term in name for term in ["chicken", "mutton", "biriyani", "biryani", "briyani", "egg", "meat", "fish", "pork", "beef"])
                    xp += 20 if not is_animal else 5
                elif category == "waste":
                    is_recycling = any(term in name for term in ["recycle", "recycling"])
                    xp += 30 if is_recycling else 10
                elif category in ["energy", "electricity", "appliances"]:
                    # check if AC usage is low
                    is_ac = "ac" in name or "air conditioner" in name
                    if is_ac:
                        xp += 5 if qty > 4.0 else 20
                    else:
                        xp += 20
                        
        # 2. XP from streak milestones
        if streak >= 3:
            xp += 100
        if streak >= 7:
            xp += 250
        if streak >= 30:
            xp += 1000
            
        # 3. XP from Achievements (avoid circular dependencies for level_5)
        # first_log: +50 XP
        # low_carbon_day: +100 XP
        # recycle_master: +150 XP
        # level_5: +500 XP
        has_low_carbon = False
        recycling_count = 0
        for r in records:
            tc = r.get("total_carbon", 0.0)
            if tc > 0 and tc < 1.0:
                has_low_carbon = True
            for act in r.get("activities", []):
                n = act.get("name", "").lower()
                cat = act.get("category", "").lower()
                if cat == "waste" and any(term in n for term in ["recycle", "recycling"]):
                    recycling_count += 1
                    
        if len(records) >= 1:
            xp += 50 # first_log
        if has_low_carbon:
            xp += 100 # low_carbon_day
        if streak >= 3:
            xp += 100 # streak_3
        if streak >= 7:
            xp += 250 # streak_7
        if recycling_count >= 3:
            xp += 150 # recycle_master
            
        if not exclude_level5:
            # Recheck level progress without the level 5 achievement bonus
            xp_pre = self.calculate_total_xp(records, streak, username, exclude_level5=True, db=db)
            lvl_pre = (xp_pre // 300) + 1
            if lvl_pre >= 5:
                xp += 500 # level_5
                
        # 4. XP from Dynamic Challenge Completions
        challenges = self.get_challenges(username, db=db, records=records)
        for dc in challenges["daily"]:
            if dc.completed:
                xp += dc.xp
        for wc in challenges["weekly"]:
            if wc.completed:
                xp += wc.xp
                
        return xp
