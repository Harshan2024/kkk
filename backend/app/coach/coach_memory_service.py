from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import (
    Activity, 
    ActivityEntity, 
    Analytics, 
    History, 
    Achievement, 
    SustainabilityScore, 
    UserSustainabilityProfile, 
    Goal, 
    TrendRecord,
    CoachReport
)

class CoachMemoryService:
    def __init__(self, db: Session):
        self.db = db

    def get_sustainability_profile(self, user_id: int) -> UserSustainabilityProfile:
        """
        Retrieves or initializes a user's sustainability profile.
        """
        profile = self.db.query(UserSustainabilityProfile).filter(
            UserSustainabilityProfile.user_id == user_id
        ).first()
        if not profile:
            profile = UserSustainabilityProfile(
                user_id=user_id,
                primary_lifestyle_type="Eco Balanced",
                transport_profile="Eco Commuter",
                food_profile="Balanced Diet",
                energy_profile="Moderate Energy User",
                waste_profile="Active Recycler",
                overall_maturity="Eco Beginner"
            )
            self.db.add(profile)
            try:
                self.db.commit()
                self.db.refresh(profile)
            except Exception:
                self.db.rollback()
        return profile

    def update_sustainability_profile(self, user_id: int, **kwargs) -> UserSustainabilityProfile:
        """
        Updates fields on the user's sustainability profile.
        """
        profile = self.get_sustainability_profile(user_id)
        for k, v in kwargs.items():
            if hasattr(profile, k):
                setattr(profile, k, v)
        try:
            self.db.commit()
            self.db.refresh(profile)
        except Exception:
            self.db.rollback()
        return profile

    def get_sustainability_memory(self, user_id: int) -> Dict[str, Any]:
        """
        Aggregates habit, behavior, emission profile, improvement history,
        coaching history, recommendation history, and goal history.
        """
        profile = self.get_sustainability_profile(user_id)
        
        # 1. Emission Profile (7-day and 30-day totals)
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        activities_7d = self.db.query(Activity).filter(
            Activity.user_id == user_id,
            Activity.logged_at >= week_ago
        ).all()
        
        activities_30d = self.db.query(Activity).filter(
            Activity.user_id == user_id,
            Activity.logged_at >= month_ago
        ).all()
        
        total_emissions_7d = sum(a.calculated_value for a in activities_7d)
        total_emissions_30d = sum(a.calculated_value for a in activities_30d)
        
        # Category breakdown 30d
        cat_emissions_30d = {"food": 0.0, "transport": 0.0, "energy": 0.0, "waste": 0.0}
        for a in activities_30d:
            cat = a.category.lower() if a.category else "energy"
            if cat in ["electricity", "appliances", "energy"]:
                mapped_cat = "energy"
            elif cat in ["food", "transport", "waste"]:
                mapped_cat = cat
            else:
                mapped_cat = "energy"
            cat_emissions_30d[mapped_cat] += a.calculated_value
            
        emission_profile = {
            "weekly_total": round(total_emissions_7d, 2),
            "monthly_total": round(total_emissions_30d, 2),
            "category_breakdown_30d": cat_emissions_30d
        }
        
        # 2. Habit Profile (from detected patterns or profile fields)
        habit_profile = {
            "primary_lifestyle_type": profile.primary_lifestyle_type,
            "transport_profile": profile.transport_profile,
            "food_profile": profile.food_profile,
            "energy_profile": profile.energy_profile,
            "waste_profile": profile.waste_profile,
            "overall_maturity": profile.overall_maturity
        }

        # 3. Behavior Profile (streaks, achievements)
        scores = self.db.query(SustainabilityScore).filter(
            SustainabilityScore.user_id == user_id
        ).order_by(SustainabilityScore.date.desc()).limit(30).all()
        
        from app.services.gamification_service import calculate_streaks
        streaks = calculate_streaks(self.db, user_id)
        
        achievements = self.db.query(Achievement).filter(
            Achievement.user_id == user_id
        ).all()
        
        behavior_profile = {
            "current_streak": streaks.get("current_streak", 0),
            "longest_streak": streaks.get("longest_streak", 0),
            "achievements_unlocked": [ach.name for ach in achievements],
            "recent_scores": [round(s.score, 1) for s in scores]
        }

        # 4. Goal History
        goals = self.db.query(Goal).filter(
            Goal.user_id == user_id
        ).order_by(Goal.created_at.desc()).all()
        
        goal_history = []
        for g in goals:
            goal_history.append({
                "id": g.id,
                "goal_type": g.goal_type,
                "target_value": g.target_value,
                "current_value": g.current_value,
                "status": g.status,
                "progress_percentage": g.progress_percentage,
                "created_at": g.created_at.isoformat()
            })

        # 5. Coaching & Recommendation History
        reports = self.db.query(CoachReport).filter(
            CoachReport.user_id == user_id
        ).order_by(CoachReport.created_at.desc()).limit(10).all()
        
        coaching_history = []
        recommendation_history = []
        for r in reports:
            coaching_history.append({
                "report_type": r.report_type,
                "created_at": r.created_at.isoformat(),
                "data_summary": r.report_data.get("summary") if r.report_data else None
            })
            if r.report_data and "recommendations" in r.report_data:
                recommendation_history.extend(r.report_data["recommendations"])

        return {
            "user_id": user_id,
            "habit_profile": habit_profile,
            "behavior_profile": behavior_profile,
            "emission_profile": emission_profile,
            "goal_history": goal_history,
            "coaching_history": coaching_history,
            "recommendation_history": list(set(recommendation_history))
        }
