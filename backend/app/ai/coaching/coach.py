from datetime import datetime, date, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models import Activity, AIInsight
from app.ai.recommendation.recommender import get_recommendation_candidates
from app.ai.ranking.ranker import rank_recommendations

from app.utils.safe_db import safe_query_all, safe_commit, DatabaseUnavailableException

def analyze_user_habits(db: Session, user_id: int) -> list[dict]:
    """
    Scans the user's logged activity logs and identifies behavioral patterns.
    Returns list of habit analysis reports.
    """
    habits = []
    
    # Query last 30 activities
    activities = safe_query_all(
        db.query(Activity).filter(
            Activity.user_id == user_id
        ).order_by(Activity.logged_at.desc()).limit(50)
    )
    
    if not activities:
        # Default coaching habits
        return [
            {
                "title": "Welcome, Eco Advocate!",
                "description": "No patterns detected yet. Log a few activities to unlock deep habit insights.",
                "severity": "info",
                "savings_estimate": "Unlock savings up to 40%"
            }
        ]
        
    # 1. Day of week analysis (Spikes)
    weekday_emissions = {i: [] for i in range(7)}
    for a in activities:
        # Determine day of week
        wd = a.logged_at.weekday()
        weekday_emissions[wd].append(a.calculated_value)
        
    averages = {}
    for wd, vals in weekday_emissions.items():
        if vals:
            averages[wd] = sum(vals) / len(vals)
            
    if averages:
        max_wd = max(averages, key=averages.get)
        global_avg = sum(sum(vals) for vals in weekday_emissions.values()) / len(activities)
        
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        if averages[max_wd] > global_avg * 1.25:
            percent_increase = int((averages[max_wd] - global_avg) / global_avg * 100)
            habits.append({
                "title": f"{day_names[max_wd]} Carbon Spike",
                "description": f"Your emissions are typically {percent_increase}% higher on {day_names[max_wd]}s compared to your daily average. Inspect your logs for that day.",
                "severity": "warning",
                "savings_estimate": f"Potential savings: ~{global_avg * 0.25:.1f} kg CO2e/week"
            })
            
    # 2. Category-specific checks (e.g. AC heavy usage)
    ac_runs = [a for a in activities if a.category == "appliances" and "ac" in a.item]
    if len(ac_runs) >= 3:
        total_ac_hrs = sum(a.quantity for a in ac_runs)
        if total_ac_hrs > 12.0:
            habits.append({
                "title": "High Cooling Intensity",
                "description": f"You logged {total_ac_hrs:.1f} hours of AC usage recently. AC cooling is your largest appliance footprint element.",
                "severity": "alert",
                "savings_estimate": f"Save {total_ac_hrs * 0.5:.1f} kg CO2e by raising thermostat 2 degrees"
            })
            
    # 3. Diet check
    beef_logs = [a for a in activities if a.category == "food" and a.item == "beef"]
    if beef_logs:
        total_beef = sum(a.quantity for a in beef_logs)
        habits.append({
            "title": "Red Meat Impact",
            "description": f"Beef consumption contributes heavily to food emissions. Swapping beef for poultry or curd rice lowers meal footprint significantly.",
            "severity": "warning",
            "savings_estimate": f"Potential savings: ~{total_beef * 53.0:.1f} kg CO2e"
        })
        
    # Default fallback if no specific spikes found
    if not habits:
        habits.append({
            "title": "Stable Baseline",
            "description": "Your sustainability logs show a well-distributed carbon footprint with no sudden spikes.",
            "severity": "success",
            "savings_estimate": "Keep maintaining this low impact!"
        })
        
    return habits

def generate_personalized_recommendations(db: Session, user_id: int) -> list[AIInsight]:
    """
    Retrieves recommendation candidates, ranks them using the Ranker engine, 
    and saves the top ranked items to the AIInsight table.
    """
    candidates = get_recommendation_candidates()
    ranked = rank_recommendations(candidates)
    
    # Check read-only state before performing database write operations
    from app.database import session as db_session
    if db_session.READ_ONLY_MODE:
        raise DatabaseUnavailableException("Database temporarily unavailable. Read-only mode active.")
        
    # Clear active insights safely
    def _delete_insights():
        db.query(AIInsight).filter(
            AIInsight.user_id == user_id, 
            AIInsight.is_active == 1
        ).delete()
    
    from app.utils.safe_db import run_db_with_retry
    run_db_with_retry(_delete_insights, "delete_insights", db=db)
    
    insights = []
    # Save top 4 ranked recommendations
    for c in ranked[:4]:
        ins = AIInsight(
            user_id=user_id,
            content=c["content"],
            category=c["category"],
            impact_estimate=f"Saves {c['impact_value']} kg CO2e/month",
            impact_level="HIGH" if c["impact_value"] > 25 else "MEDIUM" if c["impact_value"] > 8 else "LOW",
            impact_value=c["impact_value"],
            feasibility=c["feasibility"],
            difficulty=c["difficulty"],
            confidence_score=c["confidence_score"],
            sustainability_gain=c["sustainability_gain"],
            behavioral_compatibility=c.get("behavioral_compatibility", 5.0),
            why_explanation=c.get("why_explanation"),
            how_calculation=c.get("how_calculation"),
            weighted_priority_score=c.get("weighted_priority_score", 0.0),
            is_active=1
        )
        db.add(ins)
        insights.append(ins)
        
    safe_commit(db, "save_recommendations")
    return insights
