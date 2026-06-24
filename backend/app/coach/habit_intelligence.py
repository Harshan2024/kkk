from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Activity, UserSustainabilityProfile, AIInsight, User
from app.coach.habit_analyzer import analyze_habits

class HabitIntelligenceEngine:
    def __init__(self, db: Session):
        self.db = db

    def analyze_and_update(self, user_id: int, username: str) -> Dict[str, Any]:
        """
        Analyzes the user's logged activities from PostgreSQL, determines their
        lifestyle habits and sustainability profile, and stores findings in
        user_sustainability_profiles and ai_insights.
        """
        # Fetch user's historical activities
        activities = self.db.query(Activity).filter(Activity.user_id == user_id).all()
        
        # 1. Transform Activities into records format expected by analyze_habits helper
        records = []
        # Group activities by day to form "records"
        grouped_activities: Dict[str, List[Dict[str, Any]]] = {}
        for act in activities:
            day_str = act.logged_at.strftime("%Y-%m-%d")
            if day_str not in grouped_activities:
                grouped_activities[day_str] = []
            
            grouped_activities[day_str].append({
                "name": act.item,
                "category": act.category,
                "quantity": act.quantity,
                "unit": act.unit,
                "carbon": act.calculated_value
            })
            
        for day_str, acts in grouped_activities.items():
            records.append({
                "timestamp": f"{day_str}T00:00:00Z",
                "total_carbon": sum(a["carbon"] for a in acts),
                "activities": acts
            })
            
        # Run analyze_habits
        analysis = analyze_habits(records)
        
        # 2. Extract Specific Profiles
        food_profile = analysis["food"].food_profile or "balanced_diet"
        transport_profile = analysis["transport"].transport_profile or "eco_commuter"
        
        # Energy profile
        ac_hours = analysis["energy"].ac_hours
        if ac_hours > 4.0:
            energy_profile = "high_ac_usage"
        elif ac_hours > 0.0:
            energy_profile = "moderate_energy_user"
        else:
            energy_profile = "eco_energy_saver"
            
        # Waste profile
        recycling_freq = analysis["waste"].recycling_frequency
        if recycling_freq > 3:
            waste_profile = "active_recycler"
        elif recycling_freq > 0:
            waste_profile = "moderate_recycler"
        else:
            waste_profile = "eco_waste_saver"

        # 3. Daily / Weekly / Monthly logging patterns
        total_days = len(grouped_activities)
        if total_days >= 30:
            logging_pattern = "monthly_consistent"
        elif total_days >= 7:
            logging_pattern = "weekly_active"
        elif total_days >= 1:
            logging_pattern = "daily_beginner"
        else:
            logging_pattern = "inactive"

        # Determine overall sustainability maturity
        user = self.db.query(User).filter(User.id == user_id).first()
        xp = user.xp if user else 0
        if xp >= 2250:
            overall_maturity = "Eco Champion"
        elif xp >= 1250:
            overall_maturity = "Eco Consistent"
        elif xp >= 650:
            overall_maturity = "Eco Improving"
        elif xp >= 250:
            overall_maturity = "Eco Aware"
        else:
            overall_maturity = "Eco Beginner"

        # Primary lifestyle type based on highest category emissions in last 30 days
        cat_emissions = {"food": 0.0, "transport": 0.0, "energy": 0.0, "waste": 0.0}
        month_ago = datetime.utcnow() - timedelta(days=30)
        activities_30d = [a for a in activities if a.logged_at >= month_ago]
        for a in activities_30d:
            cat = a.category.lower() if a.category else "energy"
            if cat in ["electricity", "appliances", "energy"]:
                mapped_cat = "energy"
            elif cat in ["food", "transport", "waste"]:
                mapped_cat = cat
            else:
                mapped_cat = "energy"
            cat_emissions[mapped_cat] += a.calculated_value
            
        primary_lifestyle = "Eco Balanced"
        if any(cat_emissions.values()):
            max_cat = max(cat_emissions, key=cat_emissions.get)
            primary_lifestyle = f"{max_cat.capitalize()} Heavy"

        # 4. Save/Update User Sustainability Profile in DB
        profile = self.db.query(UserSustainabilityProfile).filter(
            UserSustainabilityProfile.user_id == user_id
        ).first()
        if not profile:
            profile = UserSustainabilityProfile(
                user_id=user_id,
                primary_lifestyle_type=primary_lifestyle,
                transport_profile=transport_profile,
                food_profile=food_profile,
                energy_profile=energy_profile,
                waste_profile=waste_profile,
                overall_maturity=overall_maturity
            )
            self.db.add(profile)
        else:
            profile.primary_lifestyle_type = primary_lifestyle
            profile.transport_profile = transport_profile
            profile.food_profile = food_profile
            profile.energy_profile = energy_profile
            profile.waste_profile = waste_profile
            profile.overall_maturity = overall_maturity
            profile.updated_at = datetime.utcnow()
            
        # 5. Behavior Shifts: Compare this week vs prior week emissions
        this_week_start = datetime.utcnow() - timedelta(days=7)
        prior_week_start = datetime.utcnow() - timedelta(days=14)
        
        emissions_this_week = sum(a.calculated_value for a in activities if a.logged_at >= this_week_start)
        emissions_prior_week = sum(a.calculated_value for a in activities if prior_week_start <= a.logged_at < this_week_start)
        
        shift_text = ""
        if emissions_prior_week > 0:
            diff_pct = ((emissions_this_week - emissions_prior_week) / emissions_prior_week) * 100
            if diff_pct < -5.0:
                shift_text = f"Your weekly carbon emissions dropped by {abs(diff_pct):.1f}% compared to the prior week! Great job!"
            elif diff_pct > 5.0:
                shift_text = f"Warning: Weekly carbon emissions increased by {diff_pct:.1f}% compared to the prior week. Try reducing appliance runtimes."
            else:
                shift_text = "Your weekly carbon footprint is stable compared to the prior week."
        else:
            shift_text = "Log activities consistently across weeks to track behavior shifts and weekly reduction performance."

        try:
            self.db.commit()
            self.db.refresh(profile)
        except Exception:
            self.db.rollback()

        # 6. Save Habit Findings as Insights in ai_insights
        # We can delete old insights of type "habit"
        try:
            self.db.query(AIInsight).filter(
                AIInsight.user_id == user_id,
                AIInsight.insight_type == "habit"
            ).delete()
            
            habit_insight = AIInsight(
                user_id=user_id,
                content=f"Detected patterns: Transport profile is '{transport_profile.replace('_', ' ')}', Food profile is '{food_profile.replace('_', ' ')}'.",
                category="lifestyle",
                insight_type="habit",
                priority="MEDIUM",
                confidence=0.90,
                user_relevance_score=8.5,
                impact_estimate="Maturity Level Up",
                impact_level="MEDIUM",
                impact_value=10.0,
                why_explanation=shift_text
            )
            self.db.add(habit_insight)
            self.db.commit()
        except Exception as e:
            self.db.rollback()

        return {
            "primary_lifestyle_type": primary_lifestyle,
            "transport_profile": transport_profile,
            "food_profile": food_profile,
            "energy_profile": energy_profile,
            "waste_profile": waste_profile,
            "overall_maturity": overall_maturity,
            "logging_pattern": logging_pattern,
            "behavior_shift": shift_text
        }
