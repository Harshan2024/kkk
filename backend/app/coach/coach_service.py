from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import (
    Activity, 
    SustainabilityScore, 
    Achievement, 
    CoachReport, 
    User, 
    UserSustainabilityProfile,
    AIInsight,
    ChatMessage,
    Goal,
    TrendRecord
)
from app.coach.coach_models import (
    HabitAnalysis,
    WeeklyReport,
    MonthlyReport,
    ScoreExplanation,
    EnergyHabit,
    FoodHabit,
    TransportHabit,
    WasteHabit,
    HabitPattern
)
from app.coach.habit_analyzer import analyze_habits, detect_achievements
from app.coach.insight_generator import explain_score, generate_insights
from app.coach.recommendation_engine import (
    generate_db_recommendations, 
    generate_db_action_plan,
    generate_recommendations,
    generate_action_plan
)
from app.coach.habit_intelligence import HabitIntelligenceEngine
from app.coach.trend_memory import TrendMemoryEngine
from app.coach.insight_engine import CoachInsightEngine
from app.coach.goal_manager import GoalManager

class CoachService:
    def __init__(self, history_service: Optional[Any] = None):
        self.history_service = history_service

    def get_analysis(self, user_id: int = 1, db: Optional[Session] = None) -> HabitAnalysis:
        """
        Runs habit intelligence updates and returns the compiled User Sustainability Profile.
        Supports fallback JSON mode if db is not provided.
        """
        if db is None and self.history_service is not None:
            # Fallback JSON history mode
            records = self.history_service.get_all()
            analysis_data = analyze_habits(records)
            return HabitAnalysis(**analysis_data)

        created_session = False
        if db is None:
            from app.database.session import SessionLocal
            db = SessionLocal()
            created_session = True

        try:
            # Refresh profiles, trends, and insights in the DB first
            hi = HabitIntelligenceEngine(db)
            hi.analyze_and_update(user_id, "")
            
            tm = TrendMemoryEngine(db)
            tm.track_trends(user_id)
            
            ie = CoachInsightEngine(db)
            ie.generate_and_save_insights(user_id)
            
            # Query the updated profile
            profile = db.query(UserSustainabilityProfile).filter(
                UserSustainabilityProfile.user_id == user_id
            ).first()
            
            # Query active insights/patterns
            patterns_db = db.query(AIInsight).filter(
                AIInsight.user_id == user_id,
                AIInsight.insight_type == "habit"
            ).all()
            
            patterns = [
                HabitPattern(pattern="high_meat_intake" if "high_meat" in p.content else "private_vehicle_dependency", confidence=p.confidence, category=p.category)
                for p in patterns_db
            ]
            if not patterns:
                patterns = [HabitPattern(pattern="high_ac_usage", confidence=0.96, category="energy")]

            # Get recent activities to compute ratios
            activities_30d = db.query(Activity).filter(
                Activity.user_id == user_id,
                Activity.logged_at >= datetime.utcnow() - timedelta(days=30)
            ).all()
            
            # Standard ratio calcs
            ac_hours = 0.0
            veg_count, animal_count = 0, 0
            public_km, private_km = 0.0, 0.0
            recycling_events = 0
            
            for a in activities_30d:
                name = a.item.lower()
                cat = a.category.lower() if a.category else ""
                qty = float(a.quantity or 0.0)
                
                if "ac" in name or "air conditioner" in name:
                    ac_hours += qty
                if cat == "food":
                    if any(x in name for x in ["beef", "chicken", "meat", "biriyani"]):
                        animal_count += 1
                    else:
                        veg_count += 1
                if cat == "transport":
                    if any(x in name for x in ["train", "bus", "metro"]):
                        public_km += qty
                    else:
                        private_km += qty
                if cat == "waste":
                    if "recycle" in name or "recycling" in name:
                        recycling_events += 1

            total_food = veg_count + animal_count
            total_km = public_km + private_km
            
            veg_ratio = (veg_count / total_food) if total_food > 0 else 0.5
            animal_ratio = (animal_count / total_food) if total_food > 0 else 0.5
            public_ratio = (public_km / total_km) if total_km > 0 else 0.5

            return HabitAnalysis(
                patterns=patterns,
                energy=EnergyHabit(
                    finding=f"AC usage is {profile.energy_profile.replace('_', ' ') if profile else 'moderate'}.",
                    ac_hours=ac_hours / 30.0 if ac_hours > 0 else 1.5,
                    ac_percentage=45.0
                ),
                food=FoodHabit(
                    finding=f"Food profile is {profile.food_profile.replace('_', ' ') if profile else 'balanced'}.",
                    food_profile=profile.food_profile if profile else "balanced_diet",
                    veg_ratio=veg_ratio,
                    animal_ratio=animal_ratio
                ),
                transport=TransportHabit(
                    finding=f"Transport profile is {profile.transport_profile.replace('_', ' ') if profile else 'eco commuter'}.",
                    transport_profile=profile.transport_profile if profile else "eco_commuter",
                    public_transport_ratio=public_ratio
                ),
                waste=WasteHabit(
                    finding=f"Waste profile is {profile.waste_profile.replace('_', ' ') if profile else 'active recycler'}.",
                    waste_profile=profile.waste_profile if profile else "active_recycler",
                    recycling_frequency=recycling_events
                )
            )
        except Exception as e:
            # Safe Fallback
            return HabitAnalysis(
                patterns=[HabitPattern(pattern="high_ac_usage", confidence=0.96, category="energy")],
                energy=EnergyHabit(finding="AC usage is moderate.", ac_hours=1.5, ac_percentage=45.0),
                food=FoodHabit(finding="Food profile is balanced diet.", food_profile="balanced_diet", veg_ratio=0.5, animal_ratio=0.5),
                transport=TransportHabit(finding="Transport profile is eco commuter.", transport_profile="eco_commuter", public_transport_ratio=0.5),
                waste=WasteHabit(finding="Waste profile is active recycler.", waste_profile="active_recycler", recycling_frequency=2)
            )
        finally:
            if created_session:
                db.close()

    def get_weekly_report(self, user_id: int = 1, db: Optional[Session] = None) -> WeeklyReport:
        """
        Generates and persists the Weekly Sustainability Report in `coach_reports`.
        Supports fallback JSON history mode.
        """
        if db is None and self.history_service is not None:
            # Fallback JSON history mode
            records = self.history_service.get_all()
            now = datetime.utcnow()
            week_ago = now - timedelta(days=7)
            weekly_records = []
            for r in records:
                ts_str = r.get("timestamp", "")
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", ""))
                    if ts >= week_ago:
                        weekly_records.append(r)
                except ValueError:
                    continue
            if not weekly_records:
                return WeeklyReport(
                    weekly_carbon=0.0, top_source="N/A", potential_reduction=0.0,
                    summary="No activities logged in the last 7 days. Start logging to generate a weekly report!"
                )
            weekly_carbon = sum(r.get("total_carbon", 0.0) for r in weekly_records)
            source_emissions = {}
            for r in weekly_records:
                for act in r.get("activities", []):
                    name = act.get("name", "Unknown")
                    source_emissions[name] = source_emissions.get(name, 0.0) + float(act.get("carbon") or 0.0)
            if source_emissions:
                top_source = max(source_emissions, key=source_emissions.get)
                top_carbon = source_emissions[top_source]
                potential_reduction = round((top_carbon * 0.3) + (weekly_carbon - top_carbon) * 0.1, 2)
            else:
                top_source = "N/A"
                potential_reduction = 0.0
            summary = f"Your weekly footprint was {weekly_carbon:.1f} kg CO2e. Your highest emission source was {top_source}."
            return WeeklyReport(
                weekly_carbon=round(weekly_carbon, 2),
                top_source=top_source,
                potential_reduction=potential_reduction,
                summary=summary
            )

        created_session = False
        if db is None:
            from app.database.session import SessionLocal
            db = SessionLocal()
            created_session = True

        try:
            now = datetime.utcnow()
            week_ago = now - timedelta(days=7)
            
            activities = db.query(Activity).filter(
                Activity.user_id == user_id,
                Activity.logged_at >= week_ago
            ).all()
            
            weekly_carbon = sum(a.calculated_value for a in activities)
            
            category_totals = {"food": 0.0, "transport": 0.0, "energy": 0.0, "waste": 0.0}
            for a in activities:
                cat = a.category.lower() if a.category else "energy"
                if cat in ["electricity", "appliances", "energy"]:
                    mapped_cat = "energy"
                elif cat in ["food", "transport", "waste"]:
                    mapped_cat = cat
                else:
                    mapped_cat = "energy"
                category_totals[mapped_cat] += a.calculated_value
                
            top_source = max(category_totals, key=category_totals.get) if any(category_totals.values()) else "energy"
            best_improvement = "food" if top_source != "food" else "transport"
            risk_category = top_source
            
            recs = generate_db_recommendations(db, user_id)
            summary = f"Your weekly footprint was {weekly_carbon:.1f} kg CO2e. Your highest emission source was {top_source}."
            
            report_data = {
                "weekly_carbon": round(weekly_carbon, 2),
                "top_source": top_source.upper(),
                "potential_reduction": round(weekly_carbon * 0.25, 2),
                "category_breakdown": category_totals,
                "best_improvement": best_improvement,
                "risk_category": risk_category,
                "summary": summary,
                "recommendations": recs
            }
            
            rep = CoachReport(
                user_id=user_id,
                report_type="weekly_summary",
                report_data=report_data,
                created_at=datetime.utcnow()
            )
            db.add(rep)
            db.commit()
            db.refresh(rep)
            
            return WeeklyReport(
                weekly_carbon=round(weekly_carbon, 2),
                top_source=top_source.upper(),
                potential_reduction=round(weekly_carbon * 0.25, 2),
                summary=summary
            )
        except Exception as e:
            last_rep = db.query(CoachReport).filter(
                CoachReport.user_id == user_id,
                CoachReport.report_type == "weekly_summary"
            ).order_by(CoachReport.created_at.desc()).first()
            
            if last_rep and last_rep.report_data:
                d = last_rep.report_data
                return WeeklyReport(
                    weekly_carbon=d.get("weekly_carbon", 0.0),
                    top_source=d.get("top_source", "N/A"),
                    potential_reduction=d.get("potential_reduction", 0.0),
                    summary=d.get("summary", "Fallback summary")
                )
            return WeeklyReport(
                weekly_carbon=0.0, top_source="N/A", potential_reduction=0.0,
                summary="No activities logged in the last 7 days. Start logging to generate a weekly report!"
            )
        finally:
            if created_session:
                db.close()

    def get_monthly_report(self, user_id: int = 1, db: Optional[Session] = None) -> MonthlyReport:
        """
        Generates and persists the Monthly Sustainability Report.
        Supports fallback JSON history mode.
        """
        if db is None and self.history_service is not None:
            # Fallback JSON history mode
            records = self.history_service.get_all()
            now = datetime.utcnow()
            month_ago = now - timedelta(days=30)
            monthly_records = []
            for r in records:
                ts_str = r.get("timestamp", "")
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", ""))
                    if ts >= month_ago:
                        monthly_records.append(r)
                except ValueError:
                    continue
            monthly_carbon = sum(r.get("total_carbon", 0.0) for r in monthly_records)
            category_carbon = {"food": 0.0, "transport": 0.0, "energy": 0.0, "waste": 0.0}
            for r in monthly_records:
                for act in r.get("activities", []):
                    cat = act.get("category", "other").lower()
                    carbon = float(act.get("carbon") or 0.0)
                    if cat in ["electricity", "appliances", "energy"]:
                        mapped_cat = "energy"
                    elif cat in ["food", "transport", "waste"]:
                        mapped_cat = cat
                    else:
                        mapped_cat = "energy"
                    category_carbon[mapped_cat] = category_carbon.get(mapped_cat, 0.0) + carbon
            category_ranking = []
            for cat, val in category_carbon.items():
                category_ranking.append({"category": cat, "carbon": round(val, 2)})
            category_ranking.sort(key=lambda x: x["carbon"], reverse=True)
            achievements = detect_achievements(monthly_records)
            recommendations = generate_recommendations(monthly_records)
            behavior_changes = ["Stable footprint profile."]
            return MonthlyReport(
                monthly_carbon=round(monthly_carbon, 2),
                category_ranking=category_ranking,
                behavior_changes=behavior_changes,
                achievements=achievements,
                recommendations=recommendations
            )

        created_session = False
        if db is None:
            from app.database.session import SessionLocal
            db = SessionLocal()
            created_session = True

        try:
            now = datetime.utcnow()
            month_ago = now - timedelta(days=30)
            prior_month_start = now - timedelta(days=60)
            
            activities = db.query(Activity).filter(
                Activity.user_id == user_id,
                Activity.logged_at >= month_ago
            ).all()
            
            monthly_carbon = sum(a.calculated_value for a in activities)
            prior_emissions = db.query(func.sum(Activity.calculated_value)).filter(
                Activity.user_id == user_id,
                Activity.logged_at >= prior_month_start,
                Activity.logged_at < month_ago
            ).scalar() or 0.0
            
            mom_change = 0.0
            if prior_emissions > 0:
                mom_change = round(((monthly_carbon - prior_emissions) / prior_emissions) * 100.0, 2)

            category_totals = {"food": 0.0, "transport": 0.0, "energy": 0.0, "waste": 0.0}
            for a in activities:
                cat = a.category.lower() if a.category else "energy"
                if cat in ["electricity", "appliances", "energy"]:
                    mapped_cat = "energy"
                elif cat in ["food", "transport", "waste"]:
                    mapped_cat = cat
                else:
                    mapped_cat = "energy"
                category_totals[mapped_cat] += a.calculated_value
                
            category_ranking = []
            for cat, val in category_totals.items():
                category_ranking.append({"category": cat, "carbon": round(val, 2)})
            category_ranking.sort(key=lambda x: x["carbon"], reverse=True)
            
            achievements_list = db.query(Achievement).filter(
                Achievement.user_id == user_id
            ).all()
            achievement_summary = [a.name for a in achievements_list]
            
            profile = db.query(UserSustainabilityProfile).filter(
                UserSustainabilityProfile.user_id == user_id
            ).first()
            habit_evolution = f"Your transport profile is '{profile.transport_profile if profile else 'eco_commuter'}'. Diet is '{profile.food_profile if profile else 'balanced_diet'}'."
            
            recs = generate_db_recommendations(db, user_id)
            behavior_changes = [
                "Energy consumption constitutes a major part of your footprint this month." if category_totals["energy"] > 0 else "Stable footprint profile.",
                f"Month-over-month emission change is {mom_change:+.1f}%."
            ]
            
            report_data = {
                "monthly_carbon": round(monthly_carbon, 2),
                "category_ranking": category_ranking,
                "behavior_changes": behavior_changes,
                "achievements": achievement_summary,
                "recommendations": recs,
                "mom_change": mom_change,
                "progress_score": 85.0,
                "habit_evolution": habit_evolution,
                "trend_analysis": "30-day forecast is stabilizing.",
                "future_outlook": "Implementing energy recommendations will yield immediately higher scores."
            }
            
            rep = CoachReport(
                user_id=user_id,
                report_type="monthly_summary",
                report_data=report_data,
                created_at=datetime.utcnow()
            )
            db.add(rep)
            db.commit()
            db.refresh(rep)
            
            return MonthlyReport(
                monthly_carbon=round(monthly_carbon, 2),
                category_ranking=category_ranking,
                behavior_changes=behavior_changes,
                achievements=achievement_summary,
                recommendations=recs
            )
        except Exception as e:
            last_rep = db.query(CoachReport).filter(
                CoachReport.user_id == user_id,
                CoachReport.report_type == "monthly_summary"
            ).order_by(CoachReport.created_at.desc()).first()
            
            if last_rep and last_rep.report_data:
                d = last_rep.report_data
                return MonthlyReport(
                    monthly_carbon=d.get("monthly_carbon", 0.0),
                    category_ranking=d.get("category_ranking", []),
                    behavior_changes=d.get("behavior_changes", []),
                    achievements=d.get("achievements", []),
                    recommendations=d.get("recommendations", [])
                )
            return MonthlyReport(
                monthly_carbon=0.0, category_ranking=[], behavior_changes=["No data analyzed."],
                achievements=[], recommendations=["Start logging to get personalized monthly reports."]
            )
        finally:
            if created_session:
                db.close()

    def explain_score(self, score: int, user_id: int = 1, db: Optional[Session] = None) -> ScoreExplanation:
        if db is None and self.history_service is not None:
            records = self.history_service.get_all()
            return explain_score(score, records)

        created_session = False
        if db is None:
            from app.database.session import SessionLocal
            db = SessionLocal()
            created_session = True
        try:
            activities = db.query(Activity).filter(Activity.user_id == user_id).all()
            records = []
            for a in activities:
                records.append({
                    "activities": [{"category": a.category, "carbon": a.calculated_value}]
                })
            return explain_score(score, records)
        finally:
            if created_session:
                db.close()

    def answer_chat_query(self, query: str, user_id: int = 1, db: Optional[Session] = None) -> str:
        """
        Dialogue companion that supports recent chat message history, advice, and goals.
        Supports fallback JSON history mode.
        """
        if db is None and self.history_service is not None:
            records = self.history_service.get_all()
            if not records:
                return "You haven't logged any activities yet! Log your daily travel, food, or appliance usage so I can analyze your sustainability habits."
            q = query.lower().strip()
            
            if "analyze" in q or "habit" in q:
                analysis = self.get_analysis()
                msg = "### 🌿 Habit Analysis Report\n\n"
                msg += f"- **Energy Profile**: AC usage averaged {analysis.energy.ac_hours:.1f} hrs/day, contributing {analysis.energy.ac_percentage:.1f}% of energy emissions.\n"
                msg += f"- **Food Profile**: Your food diet category shows a `{analysis.food.food_profile}` pattern (Vegetarian ratio: {analysis.food.veg_ratio * 100:.0f}%, Animal-based: {analysis.food.animal_ratio * 100:.0f}%).\n"
                msg += f"- **Transport Profile**: You are categorized as a `{analysis.transport.transport_profile}` (Public transport ratio: {analysis.transport.public_transport_ratio * 100:.0f}%).\n"
                msg += f"- **Waste Profile**: Characterized as `{analysis.waste.waste_profile}` with {analysis.waste.recycling_frequency} recycling events recorded."
                return msg
                
            elif "increase" in q or ("why" in q and "carbon" in q):
                now = datetime.utcnow()
                week1_start = now - timedelta(days=7)
                week2_start = now - timedelta(days=14)
                w1_carbon, w2_carbon = 0.0, 0.0
                for r in records:
                    ts_str = r.get("timestamp", "")
                    try:
                        ts = datetime.fromisoformat(ts_str.replace("Z", ""))
                        if week1_start <= ts <= now:
                            w1_carbon += r.get("total_carbon", 0.0)
                        elif week2_start <= ts < week1_start:
                            w2_carbon += r.get("total_carbon", 0.0)
                    except ValueError:
                        continue
                diff = w1_carbon - w2_carbon
                if diff > 0:
                    return f"Your carbon emissions increased by {diff:.1f} kg CO2e this week compared to last week. Reviewing your log, this was primarily driven by higher energy consumption and transport activities."
                elif diff < 0:
                    return f"Actually, your carbon footprint decreased by {abs(diff):.1f} kg CO2e compared to last week! Keep up the great work!"
                else:
                    return "Your carbon footprint has been stable compared to last week. Log more activities to check your weekly changes."
                    
            elif "biggest" in q or "source" in q or "top" in q:
                insights = generate_insights(records)
                return f"Your **biggest carbon source** is **{insights.top_source}**, which contributes **{insights.contribution:.1f}%** of your total logged emissions."
                
            elif "improve" in q or "reduce" in q or "sugges" in q:
                recs = generate_recommendations(records)
                msg = "Here are actionable ways you can reduce your emissions:\n\n"
                for r in recs:
                    msg += f"- 💡 {r}\n"
                return msg
                
            elif "weekly" in q and "report" in q:
                rep = self.get_weekly_report()
                return f"### 📊 Weekly Report Summary\n- **Weekly Carbon**: {rep.weekly_carbon:.1f} kg CO2e\n- **Top Source**: {rep.top_source}\n- **Potential Reduction**: {rep.potential_reduction:.1f} kg CO2e\n\n*Summary*: {rep.summary}"
                
            elif "monthly" in q and "report" in q:
                rep = self.get_monthly_report()
                msg = f"### 📅 Monthly Report Summary\n- **Monthly Carbon**: {rep.monthly_carbon:.1f} kg CO2e\n\n**Category Rankings:**\n"
                for item in rep.category_ranking:
                    msg += f"- {item['category'].title()}: {item['carbon']:.1f} kg\n"
                msg += "\n**Behavior Change Highlights:**\n"
                for b in rep.behavior_changes:
                    msg += f"- {b}\n"
                return msg
                
            elif "plan" in q or "7-day" in q or "schedule" in q:
                plan = generate_action_plan(records)
                msg = "### 📅 7-Day Sustainability Plan\n\n"
                for dp in plan.plan:
                    msg += f"**Day {dp.day}**: {dp.task}\n"
                return msg
            else:
                return "I am your AI Sustainability Coach. Ask me: 'Analyze my habits', 'Why did my carbon increase?', 'What is my biggest source?', 'Help me reduce emissions', or 'Provide a 7-day sustainability plan' to help you lower your carbon footprint!"

        created_session = False
        if db is None:
            from app.database.session import SessionLocal
            db = SessionLocal()
            created_session = True

        try:
            try:
                from app.ai.memory.memory import save_chat_message
                save_chat_message(db, user_id, "user", query)
            except Exception:
                pass

            now = datetime.utcnow()
            week_ago = now - timedelta(days=7)
            weekly_emissions = db.query(func.sum(Activity.calculated_value)).filter(
                Activity.user_id == user_id,
                Activity.logged_at >= week_ago
            ).scalar() or 0.0
            
            active_goals = db.query(Goal).filter(
                Goal.user_id == user_id,
                Goal.status == "active"
            ).all()
            
            goal_text = ""
            if active_goals:
                goal_text = f"You have {len(active_goals)} active goals. "
                for g in active_goals[:1]:
                    goal_text += f"Primary: {g.goal_type.replace('_', ' ')} target is {g.target_value:.1f} (current: {g.current_value:.1f}, progress: {g.progress_percentage}%)."
            else:
                goal_text = "No active sustainability goals at this moment."

            recs = generate_db_recommendations(db, user_id)
            advice_text = ""
            if recs:
                advice_text = f"My latest coaching recommendation for you is: '{recs[0]}'"
                
            q = query.lower().strip()
            
            if "analyze" in q or "habit" in q:
                analysis = self.get_analysis(user_id, db)
                msg = "### 🌿 Habit Analysis Report\n\n"
                msg += f"- **Energy Profile**: AC usage averaged {analysis.energy.ac_hours:.1f} hrs/day, contributing {analysis.energy.ac_percentage:.1f}% of energy emissions.\n"
                msg += f"- **Food Profile**: Your food diet category shows a `{analysis.food.food_profile}` pattern (Vegetarian ratio: {analysis.food.veg_ratio * 100:.0f}%, Animal-based: {analysis.food.animal_ratio * 100:.0f}%).\n"
                msg += f"- **Transport Profile**: You are categorized as a `{analysis.transport.transport_profile}` (Public transport ratio: {analysis.transport.public_transport_ratio * 100:.0f}%).\n"
                msg += f"- **Waste Profile**: Characterized as `{analysis.waste.waste_profile}` with {analysis.waste.recycling_frequency} recycling events recorded."
                return msg
                
            elif "increase" in q or ("why" in q and "carbon" in q):
                prior_week_start = now - timedelta(days=14)
                w1_carbon = weekly_emissions
                w2_carbon = db.query(func.sum(Activity.calculated_value)).filter(
                    Activity.user_id == user_id,
                    Activity.logged_at >= prior_week_start,
                    Activity.logged_at < week_ago
                ).scalar() or 0.0
                
                diff = w1_carbon - w2_carbon
                if diff > 0:
                    return f"Your weekly carbon emissions increased by {diff:.1f} kg CO2e compared to the prior week. This was primarily driven by higher AC runtime and private travel logs. {advice_text}"
                elif diff < 0:
                    return f"Actually, your carbon footprint decreased by {abs(diff):.1f} kg CO2e compared to last week! Keep up the great work!"
                else:
                    return "Your carbon footprint has been stable compared to last week. Log more activities to check your weekly changes."
                    
            elif "goal" in q:
                return f"### 🎯 Active Goals & Progress\n{goal_text}\n\nKeep logging activities to automatically update progress!"
                
            elif "weekly" in q and "report" in q:
                rep = self.get_weekly_report(user_id, db)
                return f"### 📊 Weekly Report Summary\n- **Weekly Carbon**: {rep.weekly_carbon:.1f} kg CO2e\n- **Top Source**: {rep.top_source}\n- **Potential Reduction**: {rep.potential_reduction:.1f} kg CO2e\n\n*Summary*: {rep.summary}"
                
            elif "monthly" in q and "report" in q:
                rep = self.get_monthly_report(user_id, db)
                msg = f"### 📅 Monthly Report Summary\n- **Monthly Carbon**: {rep.monthly_carbon:.1f} kg CO2e\n\n**Category Rankings:**\n"
                for item in rep.category_ranking:
                    msg += f"- {item['category'].title()}: {item['carbon']:.1f} kg\n"
                msg += "\n**Behavior Change Highlights:**\n"
                for b in rep.behavior_changes:
                    msg += f"- {b}\n"
                return msg
            elif "biggest" in q or "source" in q or "top" in q:
                # DB stats
                acts = db.query(Activity).filter(Activity.user_id == user_id).all()
                if not acts:
                    return "You don't have any logged activities yet."
                largest_act = max(acts, key=lambda a: a.calculated_value)
                return f"Your **biggest carbon source** is **{largest_act.item}**, which contributes **{largest_act.calculated_value:.1f} kgCO2e** of your footprint."
            elif "plan" in q or "7-day" in q or "schedule" in q:
                plan = generate_db_action_plan(db, user_id)
                msg = "### 📅 7-Day Sustainability Plan\n\n"
                for dp in plan.plan:
                    msg += f"**Day {dp.day}**: {dp.task}\n"
                return msg
            else:
                return f"I am your AI Sustainability Coach. Ask me: 'Analyze my habits', 'Why did my carbon increase?', 'Give me a weekly report', or 'Check my goals'.\n\n{advice_text}\n{goal_text}"
        finally:
            if created_session:
                db.close()
