from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models import (
    UserSustainabilityProfile, 
    TrendRecord, 
    Achievement, 
    Activity, 
    CoachReport,
    Goal
)
from app.coach.coach_models import DayPlan, ActionPlan

CANDIDATES = [
    {"id": "rec_ac_1h", "category": "energy", "text": "Reduce AC runtime by 1 hour daily to save emissions."},
    {"id": "rec_ac_temp", "category": "energy", "text": "Set AC temperature to 24°C instead of cooler targets."},
    {"id": "rec_veg_lunch", "category": "food", "text": "Choose a completely vegetarian lunch for immediate food footprint drop."},
    {"id": "rec_meat_limit", "category": "food", "text": "Limit meat meals (like chicken/beef) to 2 servings weekly."},
    {"id": "rec_walk_short", "category": "transport", "text": "Walk or cycle for trips under 2 km instead of driving."},
    {"id": "rec_public_transit", "category": "transport", "text": "Use public transit (bus/train) for daily commutes."},
    {"id": "rec_recycle_sort", "category": "waste", "text": "Separate recyclable plastics and paper from landfill bins."},
    {"id": "rec_e_waste", "category": "waste", "text": "Dispose of electronic waste and old chargers at designated recycle centers."}
]

def generate_recommendations(records: List[Dict[str, Any]]) -> List[str]:
    """
    Generates list of actionable recommendations based on carbon ratios.
    """
    category_carbon = {"food": 0.0, "transport": 0.0, "energy": 0.0, "waste": 0.0}
    total_carbon = 0.0
    
    for r in records:
        activities = r.get("activities", [])
        for act in activities:
            cat = act.get("category", "other").lower()
            carbon = float(act.get("carbon") or 0.0)
            
            if cat in ["electricity", "appliances", "energy"]:
                mapped_cat = "energy"
            elif cat in ["food", "transport", "waste"]:
                mapped_cat = cat
            else:
                mapped_cat = "energy"
                
            category_carbon[mapped_cat] = category_carbon.get(mapped_cat, 0.0) + carbon
            total_carbon += carbon
            
    recommendations = []
    
    if total_carbon > 0.0:
        food_pct = (category_carbon["food"] / total_carbon) * 100.0
        transport_pct = (category_carbon["transport"] / total_carbon) * 100.0
        energy_pct = (category_carbon["energy"] / total_carbon) * 100.0
        waste_pct = (category_carbon["waste"] / total_carbon) * 100.0
        
        if food_pct > 40.0:
            recommendations.append("Reduce meat meals by 2 servings/week")
        if transport_pct > 40.0:
            recommendations.append("Increase train or bus usage")
        if energy_pct > 35.0:
            recommendations.append("Reduce AC runtime")
        if waste_pct > 25.0:
            recommendations.append("Improve recycling habits")
            
    # Add default recommendation if list is empty
    if not recommendations:
        recommendations.append("Swap short driving trips with walking or cycling to build a healthy routine.")
        recommendations.append("Consider turning off air conditioning 1 hour earlier daily.")
        
    return recommendations


def generate_db_recommendations(db: Session, user_id: int) -> List[str]:
    """
    Upgraded recommendation engine (Section 6) that reads PostgreSQL metrics:
    - UserSustainabilityProfile
    - TrendRecord
    - Achievements
    - Current activities / analytics
    - Previous recommendations (for diversity)
    """
    # 1. Retrieve profiles & trends
    profile = db.query(UserSustainabilityProfile).filter(
        UserSustainabilityProfile.user_id == user_id
    ).first()
    
    trend = db.query(TrendRecord).filter(
        TrendRecord.user_id == user_id,
        TrendRecord.period_days == 30
    ).first()
    
    # 2. Retrieve unlocked achievements
    achievements = db.query(Achievement).filter(
        Achievement.user_id == user_id
    ).all()
    unlocked_names = {a.name for a in achievements}

    # 3. Retrieve previous recommendations from coach reports
    prev_recs = []
    past_reports = db.query(CoachReport).filter(
        CoachReport.user_id == user_id
    ).order_by(CoachReport.created_at.desc()).limit(5).all()
    for r in past_reports:
        if r.report_data and "recommendations" in r.report_data:
            prev_recs.extend(r.report_data["recommendations"])
    prev_recs_set = set(prev_recs)

    # 4. Rank candidates
    ranked_candidates = []
    for c in CANDIDATES:
        score = 50.0
        
        # Profile bonus
        if profile:
            lifestyle = (profile.primary_lifestyle_type or "").lower()
            if c["category"] in lifestyle:
                score += 25.0
                
        # Trend bonus/penalty
        if trend:
            if c["category"] == trend.most_problematic_category:
                score += 20.0
            if c["category"] == trend.most_improved_category:
                score -= 10.0
                
        # Achievements nudge
        if c["category"] == "transport" and "Green Commuter" not in unlocked_names:
            score += 10.0
        if c["category"] == "food" and "Plant-based Champion" not in unlocked_names:
            score += 10.0
            
        # Diversity penalty (avoid repeats)
        if c["text"] in prev_recs_set:
            score -= 35.0
            
        ranked_candidates.append((c["text"], score))

    # Sort and return top 3
    ranked_candidates.sort(key=lambda x: x[1], reverse=True)
    return [item[0] for item in ranked_candidates[:3]]

def generate_action_plan(records: List[Dict[str, Any]]) -> ActionPlan:
    """
    Fallback method matching original signature.
    """
    # Simple default plan
    plan = [
        DayPlan(day=1, task="Walk or cycle for trips under 2 km"),
        DayPlan(day=2, task="Reduce AC usage by 1 hour"),
        DayPlan(day=3, task="Choose a vegetarian meal"),
        DayPlan(day=4, task="Separate plastics and paper from trash bins"),
        DayPlan(day=5, task="Bring a reusable bottle to avoid single-use plastics"),
        DayPlan(day=6, task="Turn off appliances completely when leaving rooms"),
        DayPlan(day=7, task="Recycle any electronic waste")
    ]
    return ActionPlan(plan=plan)

def generate_db_action_plan(db: Session, user_id: int) -> ActionPlan:
    """
    Upgraded action plan tailoring tasks based on the highest emission category in the DB.
    """
    profile = db.query(UserSustainabilityProfile).filter(
        UserSustainabilityProfile.user_id == user_id
    ).first()
    
    lifestyle = (profile.primary_lifestyle_type or "balanced").lower() if profile else "balanced"
    
    plan = []
    if "energy" in lifestyle:
        plan = [
            DayPlan(day=1, task="Set AC temperature to 24°C instead of 20°C"),
            DayPlan(day=2, task="Reduce AC active time by 1 hour today"),
            DayPlan(day=3, task="Unplug 3 idle appliances that draw standby power"),
            DayPlan(day=4, task="Charge your laptop only when battery is below 20%"),
            DayPlan(day=5, task="Use natural cooling or a fan during the night instead of AC"),
            DayPlan(day=6, task="Audit lightbulbs; ensure LED alternatives are in place"),
            DayPlan(day=7, task="Implement a strict 2-hour zero AC window in the evening")
        ]
    elif "food" in lifestyle:
        plan = [
            DayPlan(day=1, task="Choose a completely vegetarian lunch"),
            DayPlan(day=2, task="Avoid animal-based takeouts (like Chicken Biriyani)"),
            DayPlan(day=3, task="Prepare a plant-based dinner with lentils or beans"),
            DayPlan(day=4, task="Buy seasonal local fruits for snack alternatives"),
            DayPlan(day=5, task="Minimize food waste by meal planning for the next 3 days"),
            DayPlan(day=6, task="Choose a dairy-free milk alternative (oat/soy) for coffee/tea"),
            DayPlan(day=7, task="Commit to a full plant-based day of eating")
        ]
    elif "transport" in lifestyle:
        plan = [
            DayPlan(day=1, task="Walk or cycle for trips under 2 km"),
            DayPlan(day=2, task="Choose public transit (train or bus) for commutes"),
            DayPlan(day=3, task="Swap 1 car journey for cycling or walking"),
            DayPlan(day=4, task="Carpool with a friend or colleague for longer trips"),
            DayPlan(day=5, task="Use electric transit options where possible"),
            DayPlan(day=6, task="Complete 5,000 steps today instead of driving"),
            DayPlan(day=7, task="Establish a car-free day over the weekend")
        ]
    else:
        plan = [
            DayPlan(day=1, task="Walk or cycle for trips under 2 km"),
            DayPlan(day=2, task="Reduce AC usage by 1 hour"),
            DayPlan(day=3, task="Choose a vegetarian meal"),
            DayPlan(day=4, task="Separate plastics and paper from trash bins"),
            DayPlan(day=5, task="Bring a reusable bottle to avoid single-use plastics"),
            DayPlan(day=6, task="Turn off appliances completely when leaving rooms"),
            DayPlan(day=7, task="Recycle any electronic waste")
        ]
        
    return ActionPlan(plan=plan)
