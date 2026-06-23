from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from app.history.history_service import HistoryService
from app.coach.coach_models import (
    HabitAnalysis,
    WeeklyReport,
    MonthlyReport,
    ScoreExplanation
)
from app.coach.habit_analyzer import analyze_habits, detect_achievements
from app.coach.insight_generator import generate_insights, explain_score
from app.coach.recommendation_engine import generate_recommendations, generate_action_plan

class CoachService:
    def __init__(self, history_service: Optional[HistoryService] = None):
        self.history_service = history_service or HistoryService()

    def get_analysis(self) -> HabitAnalysis:
        records = self.history_service.get_all()
        analysis_data = analyze_habits(records)
        return HabitAnalysis(**analysis_data)

    def get_weekly_report(self) -> WeeklyReport:
        records = self.history_service.get_all()
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        
        # Filter records in the last 7 days
        weekly_records = []
        for r in records:
            ts_str = r.get("timestamp", "")
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", ""))
                if ts >= week_ago:
                    weekly_records.append(r)
            except ValueError:
                continue
                
        # If no weekly logs, default calculations
        if not weekly_records:
            return WeeklyReport(
                weekly_carbon=0.0,
                top_source="N/A",
                potential_reduction=0.0,
                summary="No activities logged in the last 7 days. Start logging to generate a weekly report!"
            )
            
        weekly_carbon = sum(r.get("total_carbon", 0.0) for r in weekly_records)
        
        # Find highest carbon source
        source_emissions = {}
        for r in weekly_records:
            for act in r.get("activities", []):
                name = act.get("name", "Unknown")
                source_emissions[name] = source_emissions.get(name, 0.0) + float(act.get("carbon") or 0.0)
                
        if source_emissions:
            top_source = max(source_emissions, key=source_emissions.get)
            top_carbon = source_emissions[top_source]
            # Potential reduction = 30% of top source + 10% of others
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

    def get_monthly_report(self) -> MonthlyReport:
        records = self.history_service.get_all()
        now = datetime.utcnow()
        month_ago = now - timedelta(days=30)
        
        # Filter records in the last 30 days
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
        
        # Category breakdown ranking
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
        
        # Achievements & recommendations
        achievements = detect_achievements(monthly_records)
        recommendations = generate_recommendations(monthly_records)
        
        # Behavior change signals
        behavior_changes = []
        if category_carbon["energy"] > 0:
            behavior_changes.append("Energy consumption constitutes a major part of your footprint this month.")
        if category_carbon["food"] > 0:
            behavior_changes.append("A high density of food items was identified in your activity ledger.")
        if not behavior_changes:
            behavior_changes.append("Stable footprint profile. No major behavior changes identified.")
            
        return MonthlyReport(
            monthly_carbon=round(monthly_carbon, 2),
            category_ranking=category_ranking,
            behavior_changes=behavior_changes,
            achievements=achievements,
            recommendations=recommendations
        )

    def explain_score(self, score: int) -> ScoreExplanation:
        records = self.history_service.get_all()
        return explain_score(score, records)

    def answer_chat_query(self, query: str) -> str:
        """
        Processes natural language sustainability questions and returns deterministic replies.
        """
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
            
        elif "increase" in q or "why" in q and "carbon" in q:
            # Let's compare recent week vs prior week
            now = datetime.utcnow()
            week1_end = now
            week1_start = now - timedelta(days=7)
            week2_end = week1_start
            week2_start = now - timedelta(days=14)
            
            w1_carbon = 0.0
            w2_carbon = 0.0
            for r in records:
                ts_str = r.get("timestamp", "")
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", ""))
                    if week1_start <= ts <= week1_end:
                        w1_carbon += r.get("total_carbon", 0.0)
                    elif week2_start <= ts <= week2_end:
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
