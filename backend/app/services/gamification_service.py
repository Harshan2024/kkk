import logging
from datetime import datetime, date, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models import Activity, SustainabilityScore, Achievement, User
from app.utils.safe_db import safe_commit, safe_query_first, safe_count

from app.utils.logger import log_structured

class StructuredLoggerWrapper:
    def __init__(self, service_name: str):
        self.service_name = service_name
    def info(self, msg: str):
        log_structured("INFO", self.service_name, msg)
    def warning(self, msg: str):
        log_structured("WARNING", self.service_name, msg)
    def error(self, msg: str):
        import sys
        _, exc, _ = sys.exc_info()
        log_structured("ERROR", self.service_name, msg, exception=exc)
    def critical(self, msg: str):
        log_structured("CRITICAL", self.service_name, msg)

logger = StructuredLoggerWrapper("gamification_service")

# Level boundaries: (Level, Name, MinXp, MaxXp)
LEVELS = [
    (1, "Eco Beginner", 0, 250),
    (2, "Eco Explorer", 250, 650),
    (3, "Eco Guardian", 650, 1250),
    (4, "Climate Champion", 1250, 2250),
    (5, "Sustainability Leader", 2250, 3750),
    (6, "Carbon Warrior", 3750, 5750),
    (7, "Net-Zero Master", 5750, 1000000)
]

def get_level_info(xp: int) -> dict:
    """Returns level details for a given XP score."""
    for lvl, name, min_xp, max_xp in LEVELS:
        if min_xp <= xp < max_xp:
            return {
                "level": lvl,
                "name": name,
                "min_xp": min_xp,
                "max_xp": max_xp,
                "progress_pct": round(((xp - min_xp) / (max_xp - min_xp) * 100.0), 1) if (max_xp - min_xp) > 0 else 100.0
            }
    # Fallback to Max level
    return {
        "level": 7,
        "name": "Net-Zero Master",
        "min_xp": 5750,
        "max_xp": 1000000,
        "progress_pct": 100.0
    }

def calculate_streaks(db: Session, user_id: int) -> dict:
    """
    Computes daily logging, carbon reduction, and sustainability score streaks.
    Returns:
        current_streak (int): Consecutive days user logged.
        longest_streak (int): Longest consecutive logged days.
        carbon_streak (int): Consecutive days emissions <= 5.0 kg.
        score_streak (int): Consecutive days sustainability score >= 85.
        monthly_performance (list): Binary indicator of logging performance over the last 30 days.
    """
    today = date.today()
    
    # Query all daily scores sorted by date ascending
    scores = db.query(SustainabilityScore).filter(
        SustainabilityScore.user_id == user_id
    ).order_by(SustainabilityScore.date.asc()).all()
    
    if not scores:
        return {
            "current_streak": 0,
            "longest_streak": 0,
            "carbon_streak": 0,
            "score_streak": 0,
            "monthly_performance": [0] * 30
        }
        
    logged_dates = {s.date for s in scores}
    
    # 1. Daily Logging Streak
    current_streak = 0
    check_date = today
    if (today - timedelta(days=1)) not in logged_dates and today not in logged_dates:
        # Streak broken
        current_streak = 0
    else:
        # Start checking backwards from the last logged date (today or yesterday)
        check_date = today if today in logged_dates else today - timedelta(days=1)
        while check_date in logged_dates:
            current_streak += 1
            check_date -= timedelta(days=1)
            
    # Longest Logging Streak
    longest_streak = 0
    temp_streak = 0
    sorted_dates = sorted(list(logged_dates))
    
    if sorted_dates:
        temp_streak = 1
        longest_streak = 1
        for i in range(1, len(sorted_dates)):
            if sorted_dates[i] - sorted_dates[i-1] == timedelta(days=1):
                temp_streak += 1
            else:
                longest_streak = max(longest_streak, temp_streak)
                temp_streak = 1
        longest_streak = max(longest_streak, temp_streak)

    # 2. Carbon reduction streak (emissions <= 5.0 kg)
    carbon_streak = 0
    check_date = today if today in logged_dates else today - timedelta(days=1)
    while check_date in logged_dates:
        score_rec = next((s for s in scores if s.date == check_date), None)
        if score_rec and score_rec.total_emissions <= 5.0:
            carbon_streak += 1
            check_date -= timedelta(days=1)
        else:
            break
            
    # 3. Score Streak (score >= 85)
    score_streak = 0
    check_date = today if today in logged_dates else today - timedelta(days=1)
    while check_date in logged_dates:
        score_rec = next((s for s in scores if s.date == check_date), None)
        if score_rec and score_rec.score >= 85:
            score_streak += 1
            check_date -= timedelta(days=1)
        else:
            break
            
    # 4. Monthly performance array (last 30 days status)
    monthly_performance = []
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        monthly_performance.append(1 if d in logged_dates else 0)
        
    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "carbon_streak": carbon_streak,
        "score_streak": score_streak,
        "monthly_performance": monthly_performance
    }

def generate_and_track_quests(db: Session, user_id: int) -> list[dict]:
    """
    Dynamically generates sustainability quests based on recent 7-day activity metrics.
    Computes live quest progress using actual activity logs.
    """
    today = date.today()
    one_week_ago = datetime.combine(today - timedelta(days=7), datetime.min.time())
    
    # Query last 7 days activities
    activities = db.query(Activity).filter(
        Activity.user_id == user_id,
        Activity.logged_at >= one_week_ago
    ).all()
    
    # Calculate category emissions
    cat_emissions = {}
    for act in activities:
        cat_emissions[act.category] = cat_emissions.get(act.category, 0.0) + act.calculated_value
        
    total_emissions = sum(cat_emissions.values())
    
    primary_hotspot = "transport"
    if cat_emissions:
        primary_hotspot = max(cat_emissions, key=cat_emissions.get)
        
    quests = []
    
    # 1. Transport Quest
    if primary_hotspot == "transport" or cat_emissions.get("transport", 0) > total_emissions * 0.35:
        # High transport emissions -> public transit quest
        progress = sum(1 for act in activities if act.category == "transport" and act.item in ("metro", "train", "bus"))
        quests.append({
            "id": "q_trans_pub",
            "name": "The Velocity Shift",
            "description": "Use public transport twice this week.",
            "progress": min(2, progress),
            "max": 2,
            "xp": 150,
            "icon": "Bike",
            "color": "text-emerald-450 bg-emerald-500/10 border-emerald-500/20"
        })
    else:
        # Low transport -> active commute quest
        progress = sum(1 for act in activities if act.category == "transport" and act.item in ("walking", "cycling"))
        quests.append({
            "id": "q_trans_act",
            "name": "Active Commuter",
            "description": "Walk or cycle for a trip this week.",
            "progress": min(1, progress),
            "max": 1,
            "xp": 120,
            "icon": "Bike",
            "color": "text-emerald-450 bg-emerald-500/10 border-emerald-500/20"
        })
        
    # 2. Diet Quest
    if primary_hotspot == "food" or cat_emissions.get("food", 0) > total_emissions * 0.35:
        # High food emissions -> vegetarian/vegan swap
        progress = sum(1 for act in activities if act.category == "food" and act.item in ("vegetables", "curd rice", "dosa", "idli", "paneer"))
        quests.append({
            "id": "q_food_veg",
            "name": "The Green Feast",
            "description": "Eat a vegetarian or vegan meal for 3 meals.",
            "progress": min(3, progress),
            "max": 3,
            "xp": 120,
            "icon": "Leaf",
            "color": "text-emerald-450 bg-emerald-500/15 border-emerald-500/30"
        })
    else:
        # Low food emissions -> dairy check
        progress = sum(1 for act in activities if act.category == "food" and act.item == "milk")
        quests.append({
            "id": "q_food_dairy",
            "name": "Eco-Dairy Day",
            "description": "Enjoy curd/milk in moderation.",
            "progress": min(1, progress),
            "max": 1,
            "xp": 80,
            "icon": "Leaf",
            "color": "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
        })
        
    # 3. Energy / Appliance Quest
    if primary_hotspot in ("appliances", "electricity") or cat_emissions.get("appliances", 0) > total_emissions * 0.30:
        # High energy -> power saver hours limit
        progress = sum(1 for act in activities if act.category == "appliances" and act.quantity <= 2.0)
        quests.append({
            "id": "q_app_limit",
            "name": "Phantom Load Hunt",
            "description": "Limit heavy appliance usage sessions to under 2 hours.",
            "progress": min(3, progress),
            "max": 3,
            "xp": 100,
            "icon": "Plug",
            "color": "text-indigo-400 bg-indigo-500/10 border-indigo-500/20"
        })
    else:
        # Low energy -> general power saver check
        progress = sum(1 for act in activities if act.category == "appliances" and act.quantity <= 1.0)
        quests.append({
            "id": "q_app_saver",
            "name": "Power Saver",
            "description": "Use heavy appliances for 1 hour or less.",
            "progress": min(1, progress),
            "max": 1,
            "xp": 80,
            "icon": "Plug",
            "color": "text-indigo-300 bg-indigo-500/10 border-indigo-500/20"
        })
        
    # 4. Lifestyle / Waste Quest (always present)
    progress = sum(1 for act in activities if act.category == "waste" and act.item in ("recycling", "organic waste"))
    quests.append({
        "id": "q_waste_recycle",
        "name": "Zero Plastic Hero",
        "description": "Sort and recycle waste once this week.",
        "progress": min(1, progress),
        "max": 1,
        "xp": 80,
        "icon": "Recycle",
        "color": "text-emerald-550 bg-emerald-600/10 border-emerald-500/10"
    })
    
    return quests

def calculate_user_xp_and_level(db: Session, user_id: int) -> dict:
    """
    Computes total user XP and resolves their Level name and badge unlocks.
    """
    # 1. Base default XP
    total_xp = 150
    
    # 2. Add XP for logged activities
    activities = db.query(Activity).filter(Activity.user_id == user_id).all()
    for act in activities:
        # Low impact: general logs, electronics, milk
        # Medium impact: metro, bus, train, vegetarian food, electricity <= 1h
        # High impact: walking, cycling, recycling
        if act.category == "transport" and act.item in ("walking", "cycling"):
            total_xp += 30
        elif act.category == "transport" and act.item in ("metro", "train", "bus"):
            total_xp += 15
        elif act.category == "food" and act.item in ("vegetables", "curd rice", "dosa", "idli", "paneer"):
            total_xp += 15
        elif act.category == "appliances" and act.quantity <= 1.0:
            total_xp += 15
        elif act.category == "waste" and act.item in ("recycling", "organic waste"):
            total_xp += 30
        elif act.calculated_value <= 1.0:
            # General low carbon choices
            total_xp += 5
        else:
            total_xp += 2
            
    # 3. Add XP for achievements
    ach_count = db.query(Achievement).filter(Achievement.user_id == user_id).count()
    total_xp += ach_count * 50
    
    # 4. Add XP for streaks
    streaks = calculate_streaks(db, user_id)
    total_xp += streaks["current_streak"] * 10
    
    # 5. Add XP for completed quests (calculated weekly)
    quests = generate_and_track_quests(db, user_id)
    for q in quests:
        if q["progress"] >= q["max"]:
            total_xp += q["xp"]
            
    # Resolve Level Details
    lvl_details = get_level_info(total_xp)
    
    return {
        "xp": total_xp,
        "level": lvl_details["level"],
        "level_name": lvl_details["name"],
        "min_xp": lvl_details["min_xp"],
        "max_xp": lvl_details["max_xp"],
        "progress_pct": lvl_details["progress_pct"]
    }

def check_and_unlock_achievements_v2(db: Session, user_id: int, new_activity: Activity) -> list[Achievement]:
    """
    Upgraded achievements checker supporting Bronze, Silver, Gold, Platinum, and Climate Hero badges.
    Checks:
    - First Week Logged (distinct days logged >= 7, Silver)
    - 100 Activities Logged (total logs >= 100, Gold)
    - 30 Day Streak (streak >= 30, Platinum)
    - 90 Sustainability Score (SustainabilityScore.score >= 90, Gold)
    - Net-Zero Day (daily emissions <= 0.1 kg, Climate Hero)
    """
    unlocked = []
    
    def unlock(name: str, desc: str, badge_type: str):
        try:
            existing = safe_query_first(
                db.query(Achievement).filter(
                    Achievement.user_id == user_id,
                    Achievement.name == name
                )
            )
            if not existing:
                ach = Achievement(
                    user_id=user_id,
                    name=name,
                    description=desc,
                    badge_type=badge_type,
                    unlocked_at=datetime.utcnow()
                )
                db.add(ach)
                unlocked.append(ach)
        except Exception as e:
            logger.error(f"Achievement unlock check failed for '{name}': {e}")

    # Query metrics
    total_logs = safe_count(db.query(Activity).filter(Activity.user_id == user_id))
    streaks = calculate_streaks(db, user_id)
    
    # First week logged: check unique log dates
    try:
        distinct_days = db.query(func.count(func.distinct(func.date(Activity.logged_at)))).filter(
            Activity.user_id == user_id
        ).scalar()
        if distinct_days and distinct_days >= 7:
            unlock("First Week Active", "Logged carbon footprint data on 7 distinct days.", "silver")
    except Exception as e:
        logger.error(f"Distinct day validation error: {e}")

    # 100 logs
    if total_logs >= 100:
        unlock("Centurion Tracker", "Logged over 100 sustainability footprint activities.", "gold")
        
    # 30 day streak
    if streaks["current_streak"] >= 30:
        unlock("Consistent Eco-Warrior", "Maintained an active logging streak of 30 days.", "platinum")
        
    # 90 sustainability score (for today or any day)
    try:
        max_score = db.query(func.max(SustainabilityScore.score)).filter(
            SustainabilityScore.user_id == user_id
        ).scalar()
        if max_score and max_score >= 90.0:
            unlock("Model Citizen", "Achieved a daily sustainability rating of 90 or higher.", "gold")
    except Exception as e:
        logger.error(f"Max score validation error: {e}")
        
    # Net-zero day: emissions <= 0.1 kg
    today = date.today()
    start_t = datetime.combine(today, datetime.min.time())
    end_t = datetime.combine(today, datetime.max.time())
    try:
        today_emissions = db.query(func.sum(Activity.calculated_value)).filter(
            Activity.user_id == user_id,
            Activity.logged_at >= start_t,
            Activity.logged_at <= end_t
        ).scalar()
        if today_emissions is not None and today_emissions <= 0.1:
            unlock("Net-Zero Guardian", "Maintained carbon emissions under 0.1 kg for an entire day.", "climate_hero")
    except Exception as e:
        logger.error(f"Net-zero check error: {e}")

    # Original MVP triggers for backward compatibility
    if total_logs >= 1:
        unlock("Eco Pioneer", "Logged your first carbon activity!", "bronze")
        
    if new_activity.category == "transport" and new_activity.item in ("walking", "cycling", "metro", "train"):
        unlock("Green Commuter", "Opted for low-emission transport.", "silver")
        
    if new_activity.category == "food" and new_activity.item in ("curd rice", "vegetables", "dosa", "idli", "paneer"):
        unlock("Plant-based Champion", "Ate a carbon-conscious vegetarian meal.", "silver")
        
    if new_activity.category == "appliances" and new_activity.quantity <= 1.0:
        unlock("Power Saver", "Used energy-demanding appliances for 1 hour or less.", "bronze")
        
    if total_logs >= 5:
        unlock("Consistent Climateer", "Logged 5 or more activities in CarbonTracker.", "gold")

    if unlocked:
        safe_commit(db, "check_achievements")
        
    return unlocked
