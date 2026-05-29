import time
import logging
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models import Activity, SustainabilityScore, ChatMessage
from app.ai.memory.memory import save_chat_message, get_chat_history
from app.ai.coaching.coach import analyze_user_habits, generate_personalized_recommendations
from app.ai.observability.observability import track_latency

logger = logging.getLogger("carbontracker.ai.orchestrator")

def orchestrate_chat_response(db: Session, username: str, user_id: int, user_message: str) -> str:
    """
    Orchestrates the AI Sustainability Companion's conversational response.
    Analyzes historical user activities, scores, and habits to formulate personalized suggestions.
    Records model latencies in the observability dashboard metrics.
    """
    start_time = time.time()
    
    # 1. Save user message to memory history
    save_chat_message(db, user_id, "user", user_message)
    
    # Clean query
    query = user_message.lower().strip()
    
    # 2. Query user data for context
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    activities = db.query(Activity).filter(
        Activity.user_id == user_id,
        Activity.logged_at >= thirty_days_ago
    ).all()
    
    total_footprint = sum(a.calculated_value for a in activities)
    
    # Group activities by category
    cat_stats = {}
    for a in activities:
        cat_stats[a.category] = cat_stats.get(a.category, 0.0) + a.calculated_value
        
    # Find highest activity
    highest_act = None
    if activities:
        highest_act = max(activities, key=lambda x: x.calculated_value)

    # 3. Formulate the response based on intent detection
    if any(k in query for k in ["why", "increase", "footprint", "contribute", "highest"]):
        # Emission contribution analysis
        if not activities:
            response = (
                "You haven't logged any carbon footprints yet! Once you log some meals, travels, "
                "or AC usage, I can analyze exactly which activities contribute the most to your footprint."
            )
        else:
            cat_list = ", ".join(f"{cat} ({val:.1f} kg)" for cat, val in cat_stats.items())
            response = (
                f"Your total logged footprint over the past 30 days is **{total_footprint:.1f} kg CO2e**. "
                f"Here is your category distribution: {cat_list}. \n\n"
            )
            if highest_act:
                response += (
                    f"The single highest contributing log was your **{highest_act.item}** on "
                    f"{highest_act.logged_at.strftime('%A, %b %d')}, which emitted **{highest_act.calculated_value:.1f} kg CO2e** "
                    f"from the text *\"{highest_act.input_text}\"*."
                )
            response += "\n\nTo optimize this, consider switching to lower-emission alternatives for transport or appliance cooling."

    elif any(k in query for k in ["habit", "behavior", "pattern", "spike", "analyze"]):
        # Habit analysis report
        habits = analyze_user_habits(db, user_id)
        report_lines = []
        for h in habits:
            severity_emoji = "⚠️" if h["severity"] in ["warning", "alert"] else "ℹ️"
            report_lines.append(f"- **{severity_emoji} {h['title']}**: {h['description']} ({h['savings_estimate']})")
        
        response = (
            "Here is my **Smart Habit Analysis** based on your recent activity history:\n\n" +
            "\n".join(report_lines) +
            "\n\nI will continue checking your daily logs to map recurring weekday spikes or seasonal usage variations!"
        )

    elif any(k in query for k in ["recommend", "coach", "alternative", "reduce", "goal", "improve"]):
        # Coaching / Recommendations report
        insights = generate_personalized_recommendations(db, user_id)
        if not insights:
            response = "I am compiling customized suggestions for you. Continue logging activities to see them!"
        else:
            rec_lines = []
            for idx, ins in enumerate(insights, 1):
                rec_lines.append(
                    f"{idx}. **{ins.category.upper()}**: {ins.content}\n"
                    f"   *Impact*: {ins.impact_estimate} | *Feasibility*: {ins.feasibility} | *Difficulty*: {ins.difficulty}"
                )
            response = (
                "Based on your footprint, here is your prioritized **AI Sustainability Coach Plan**:\n\n" +
                "\n".join(rec_lines) +
                "\n\nWould you like me to show alternatives for any specific activity?"
            )

    elif any(k in query for k in ["hello", "hi", "hey", "greet", "who are you", "help"]):
        response = (
            "Hello! I am your **CarbonTracker AI Copilot**. 🍃\n\n"
            "I can help you monitor emissions, understand your carbon stats, and coach you towards "
            "a lower-emission lifestyle. You can ask me:\n"
            "- *'Why did my emissions increase this week?'*\n"
            "- *'Analyze my travel habits.'*\n"
            "- *'Suggest realistic sustainability improvements.'*\n\n"
            "What activity are we logging or checking today?"
        )
    else:
        # Default smart helper fallback
        response = (
            f"I analyzed your question: *\"{user_message}\"*. "
            f"Currently, your total logged emissions are **{total_footprint:.1f} kg CO2e** across {len(activities)} activities. "
            "If you would like detailed habit analysis, type *'Analyze my habits'*. "
            "For specific reduction tips, type *'Suggest improvements'*!"
        )

    # 4. Save response to chat memory
    save_chat_message(db, user_id, "assistant", response)
    
    # 5. Track Observability Latency
    track_latency("assistant", start_time)
    
    return response
