import time
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from collections import Counter

from app.models import Activity, SustainabilityScore
from app.utils.cache import global_cache


def _compute_current_streak_from_scores(scores: list) -> int:
    """
    Computes the current consecutive-day logging streak directly from
    already-fetched SustainabilityScore records.  No extra DB query needed.
    """
    if not scores:
        return 0

    today = date.today()
    logged_dates = {s.date for s in scores}

    if today not in logged_dates and (today - timedelta(days=1)) not in logged_dates:
        return 0

    check_date = today if today in logged_dates else today - timedelta(days=1)
    streak = 0
    while check_date in logged_dates:
        streak += 1
        check_date -= timedelta(days=1)
    return streak


def perform_habit_analysis(db: Session, user_id: int) -> dict:
    """
    Performs habit analysis for a given user.
    Uses app.utils.cache.global_cache to cache results for 300 seconds (5 minutes).

    Optimisation over the original version:
    - Streak is now computed inline from the already-fetched SustainabilityScore
      records, saving one extra database round-trip to `calculate_streaks`.
    """
    cache_key = f"habit_analysis_{user_id}"
    cached_data = global_cache.get(cache_key)
    if cached_data is not None:
        cached_data["cached"] = True
        return cached_data

    # ── 1. Fetch activities (last 14 days) ─────────────────────────────────────
    fourteen_days_ago = datetime.utcnow() - timedelta(days=14)
    activities = db.query(Activity).filter(
        Activity.user_id == user_id,
        Activity.logged_at >= fourteen_days_ago
    ).all()

    # Check for insufficient data
    if len(activities) < 3:
        result = {
            "generated_at": datetime.utcnow().isoformat(),
            "cached": False,
            "insufficient_data": True,
            "insights": [],
            "details": {}
        }
        global_cache.set(cache_key, result, ttl=300)
        return result

    # ── 2. Fetch sustainability scores (last 14 days) ──────────────────────────
    scores = db.query(SustainabilityScore).filter(
        SustainabilityScore.user_id == user_id,
        SustainabilityScore.date >= (date.today() - timedelta(days=14))
    ).all()
    # NOTE: No third DB call — streak is derived from `scores` below.

    # ── 3. Transport Analyzer ──────────────────────────────────────────────────
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    current_week_transport = [a for a in activities if a.category == "transport" and a.logged_at >= seven_days_ago]
    prev_week_transport    = [a for a in activities if a.category == "transport" and a.logged_at <  seven_days_ago]

    curr_transport_dist = sum(a.quantity for a in current_week_transport)
    prev_transport_dist = sum(a.quantity for a in prev_week_transport)

    curr_trans_avg = curr_transport_dist / 7.0
    prev_trans_avg = prev_transport_dist / 7.0

    transport_pct = 0.0
    if prev_trans_avg > 0:
        transport_pct = abs((curr_trans_avg - prev_trans_avg) / prev_trans_avg) * 100.0

    if curr_trans_avg < prev_trans_avg * 0.95:
        transport_status = "Improving"
    elif curr_trans_avg > prev_trans_avg * 1.05:
        transport_status = "Worsening"
    else:
        transport_status = "Stable"

    # ── 4. Energy Analyzer ────────────────────────────────────────────────────
    energy_cats = ("electricity", "appliances")

    weekdays_energy = [a for a in activities if a.category in energy_cats and a.logged_at.weekday() < 5]
    weekends_energy = [a for a in activities if a.category in energy_cats and a.logged_at.weekday() >= 5]

    weekday_avg = sum(a.calculated_value for a in weekdays_energy) / 10.0 if weekdays_energy else 0.0
    weekend_avg = sum(a.calculated_value for a in weekends_energy) / 4.0  if weekends_energy else 0.0

    weekend_spike = weekend_avg > weekday_avg * 1.15

    late_night = any(
        a.category in energy_cats and (a.logged_at.hour >= 22 or a.logged_at.hour < 5)
        for a in activities
    )

    curr_energy_acts  = [a for a in activities if a.category in energy_cats and a.logged_at >= seven_days_ago]
    curr_energy_total = sum(a.calculated_value for a in curr_energy_acts)

    energy_status = "Needs Attention" if (weekend_spike or late_night or curr_energy_total > 25.0) else "Stable"

    # ── 5. Food Analyzer ──────────────────────────────────────────────────────
    def get_food_type(item: str, item_key: str, input_text: str) -> str:
        text_check = f"{item or ''} {item_key or ''} {input_text or ''}".lower()
        non_veg = ["beef", "chicken", "fish", "mutton", "pork", "meat", "seafood", "shrimp", "egg"]
        veg     = ["milk", "curd", "cheese", "paneer", "dairy"]
        if any(w in text_check for w in non_veg):
            return "non-vegetarian"
        if any(w in text_check for w in veg):
            return "vegetarian"
        return "plant-based"

    curr_food_acts = [a for a in activities if a.category == "food" and a.logged_at >= seven_days_ago]
    prev_food_acts = [a for a in activities if a.category == "food" and a.logged_at <  seven_days_ago]

    curr_pb_count = sum(1 for a in curr_food_acts if get_food_type(a.item, getattr(a, "item_key", "") or "", a.input_text) == "plant-based")
    prev_pb_count = sum(1 for a in prev_food_acts if get_food_type(a.item, getattr(a, "item_key", "") or "", a.input_text) == "plant-based")

    food_pct_change = 0
    food_message    = "Food habits remained stable."
    food_status     = "Stable"

    if prev_pb_count > 0:
        food_pct_change = int(((curr_pb_count - prev_pb_count) / prev_pb_count) * 100)
        if food_pct_change >= 5:
            food_message = f"Plant-based meals increased by {food_pct_change}%."
            food_status  = "Improving"
        elif food_pct_change <= -5:
            food_message = f"Plant-based meals decreased by {abs(food_pct_change)}%."
            food_status  = "Needs Attention"
    elif curr_pb_count > 0:
        food_message = "Plant-based meals increased."
        food_status  = "Improving"

    # ── 6. Sustainability Score Analyzer ─────────────────────────────────────
    seven_days_ago_date = date.today() - timedelta(days=7)
    curr_scores = [s.score for s in scores if s.date >= seven_days_ago_date]
    prev_scores = [s.score for s in scores if s.date <  seven_days_ago_date]

    curr_score_avg = sum(curr_scores) / len(curr_scores) if curr_scores else 96.0
    prev_score_avg = sum(prev_scores) / len(prev_scores) if prev_scores else 96.0

    if curr_score_avg > prev_score_avg + 0.5:
        score_status = "Improving"
    elif curr_score_avg < prev_score_avg - 0.5:
        score_status = "Declining"
    else:
        score_status = "Stable"

    # ── 7. Logging Consistency ────────────────────────────────────────────────
    last_7_days_activities = [a for a in activities if a.logged_at >= seven_days_ago]
    unique_logged_days     = len(set(a.logged_at.date() for a in last_7_days_activities))
    consistency_pct        = int((unique_logged_days / 7.0) * 100.0)

    if consistency_pct >= 80:
        consistency_status = "Excellent"
    elif consistency_pct >= 50:
        consistency_status = "Good"
    else:
        consistency_status = "Needs Improvement"

    # ── 8. Risk Assessment Engine ─────────────────────────────────────────────
    curr_week_acts = [a for a in activities if a.logged_at >= seven_days_ago]

    cat_emissions: Counter = Counter()
    for a in curr_week_acts:
        cat = a.category.lower()
        if cat in ("appliances", "electricity"):
            cat = "energy"
        cat_emissions[cat] += a.calculated_value

    risk_assessment = {
        "transport": "High" if cat_emissions["transport"] > 30.0 else "Medium" if cat_emissions["transport"] > 10.0 else "Low",
        "energy":    "High" if cat_emissions["energy"]    > 25.0 else "Medium" if cat_emissions["energy"]    > 10.0 else "Low",
        "food":      "High" if cat_emissions["food"]      > 20.0 else "Medium" if cat_emissions["food"]      > 5.0  else "Low",
        "waste":     "High" if cat_emissions["waste"]     > 15.0 else "Medium" if cat_emissions["waste"]     > 5.0  else "Low",
    }

    # ── 9. Streak (inline — no extra DB query) ────────────────────────────────
    curr_streak = _compute_current_streak_from_scores(scores)

    # ── 10. AI Insight Generator (exactly 3 insights) ────────────────────────
    insights: list[str] = []

    # Insight 1: Highest Impact Problem
    highest_cat = max(cat_emissions.items(), key=lambda x: x[1])[0] if cat_emissions else "energy"
    if highest_cat == "energy" and weekend_spike:
        insights.append("Weekend electricity usage remains your highest contributor.")
    elif highest_cat == "transport" and risk_assessment["transport"] == "High":
        insights.append("Transport emissions remain your highest contributor.")
    elif highest_cat == "food" and risk_assessment["food"] == "High":
        insights.append("Food emissions remain your highest contributor.")
    else:
        insights.append(f"{highest_cat.capitalize()} emissions remain your highest contributor.")

    # Insight 2: Largest Improvement
    if transport_status == "Improving" and transport_pct > 0:
        insights.append(f"Transport emissions decreased by {int(transport_pct)}%.")
    elif food_status == "Improving" and food_pct_change > 0:
        insights.append(f"Plant-based meals increased by {food_pct_change}%.")
    elif score_status == "Improving":
        insights.append("Your Sustainability Score is showing steady improvement.")
    else:
        insights.append("Food habits remained stable.")

    # Insight 3: Positive Reinforcement
    if curr_streak >= 3:
        insights.append(f"You maintained a {curr_streak}-day activity logging streak.")
    elif consistency_status == "Excellent":
        insights.append("Your logging consistency is excellent.")
    else:
        insights.append("Keep logging daily to build your tracking habits.")

    # ── 11. Build final result ────────────────────────────────────────────────
    result = {
        "generated_at": datetime.utcnow().isoformat(),
        "cached": False,
        "insufficient_data": False,
        "insights": insights[:3],
        "details": {
            "transport":           {"status": transport_status, "confidence": 0.91},
            "energy":              {"status": energy_status,    "confidence": 0.88},
            "food":                {"status": food_status,      "confidence": 0.84},
            "score_trend":         {"status": score_status,     "confidence": 0.90},
            "logging_consistency": {"percentage": consistency_pct, "status": consistency_status},
            "risk_assessment":     risk_assessment,
        }
    }

    global_cache.set(cache_key, result, ttl=300)
    return result
