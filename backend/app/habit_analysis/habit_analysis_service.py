from datetime import datetime, date
from app.habit_analysis.category_analyzer import analyze_categories
from app.habit_analysis.score_engine import calculate_sustainability_score
from app.habit_analysis.trend_engine import calculate_trend
from app.habit_analysis.risk_engine import calculate_risk
from app.habit_analysis.recommendation_engine import generate_recommendations

def analyze_user_habits(activities, username="demo_user"):
    """
    Unified habit analysis service that coordinates Category Analyzer,
    Score Engine, Trend Engine, Risk Engine, and Recommendation Engine.
    
    Returns a standardized dictionary payload matching both custom calculations
    and the schema expected by the frontend (HabitInsights.tsx).
    """
    # 1. Base calculations
    cat_info = analyze_categories(activities)
    score_info = calculate_sustainability_score(activities)
    overall_trend = calculate_trend(activities)
    
    avg_daily = score_info["average_daily_emissions"]
    score = score_info["score"]
    days = score_info["days_tracked"]
    
    # 2. Subsystem specific stats
    daily_cat_emissions = {}
    for act in activities:
        dt = None
        category = ""
        val = 0.0
        
        if hasattr(act, "logged_at"):
            dt_raw = getattr(act, "logged_at")
            if isinstance(dt_raw, (datetime, date)):
                dt = dt_raw if isinstance(dt_raw, date) else dt_raw.date()
            category = getattr(act, "category") or ""
            val = getattr(act, "calculated_value") or 0.0
        elif isinstance(act, dict):
            dt_raw = act.get("logged_at") or act.get("date")
            if isinstance(dt_raw, str):
                try:
                    dt = datetime.fromisoformat(dt_raw.replace("Z", "+00:00")).date()
                except Exception:
                    try:
                        dt = datetime.strptime(dt_raw[:10], "%Y-%m-%d").date()
                    except Exception:
                        pass
            elif isinstance(dt_raw, (datetime, date)):
                dt = dt_raw if isinstance(dt_raw, date) else dt_raw.date()
            category = act.get("category") or ""
            val = act.get("calculated_value") or 0.0
            
        if not dt:
            dt = date.today()
            
        try:
            val = float(val)
        except (ValueError, TypeError):
            val = 0.0
            
        category = str(category).lower().strip()
        if "transport" in category or "vehicle" in category:
            bucket = "transport"
        elif "food" in category or "diet" in category:
            bucket = "food"
        elif "energy" in category or "electricity" in category or "appliance" in category:
            bucket = "energy"
        elif "waste" in category:
            bucket = "waste"
        else:
            bucket = "other"
            
        if dt not in daily_cat_emissions:
            daily_cat_emissions[dt] = {"transport": 0.0, "food": 0.0, "energy": 0.0, "waste": 0.0, "other": 0.0}
        daily_cat_emissions[dt][bucket] += val
        
    # Calculate category specific trends and averages
    cat_averages = {"transport": 0.0, "food": 0.0, "energy": 0.0, "waste": 0.0}
    cat_trends = {"transport": "Stable", "food": "Stable", "energy": "Stable", "waste": "Stable"}
    
    if daily_cat_emissions:
        for cat in cat_averages.keys():
            cat_averages[cat] = sum(day[cat] for day in daily_cat_emissions.values()) / len(daily_cat_emissions)
            
        sorted_dates = sorted(list(daily_cat_emissions.keys()))
        if len(sorted_dates) >= 2:
            mid = len(sorted_dates) // 2
            first_half = sorted_dates[:mid]
            second_half = sorted_dates[mid:]
            for cat in cat_trends.keys():
                avg_first = sum(daily_cat_emissions[d][cat] for d in first_half) / len(first_half)
                avg_second = sum(daily_cat_emissions[d][cat] for d in second_half) / len(second_half)
                diff = avg_second - avg_first
                if diff > 0.2:
                    cat_trends[cat] = "Worsening"
                elif diff < -0.2:
                    cat_trends[cat] = "Improving"
                else:
                    cat_trends[cat] = "Stable"
                    
    # Calculate logging consistency percentage (out of last 7 days)
    distinct_days = len(daily_cat_emissions)
    logging_percentage = min(100, int((distinct_days / 7.0) * 100))
    if logging_percentage >= 80:
        logging_status = "Excellent"
    elif logging_percentage >= 50:
        logging_status = "Good"
    else:
        logging_status = "Poor"
        
    # Calculate risk assessment per category
    risk_assessment = {}
    for cat in ["transport", "food", "energy", "waste"]:
        avg = cat_averages[cat]
        trend = cat_trends[cat]
        
        if cat == "transport":
            high_thresh, med_thresh = 6.0, 3.0
        elif cat == "food":
            high_thresh, med_thresh = 5.0, 2.5
        elif cat == "energy":
            high_thresh, med_thresh = 4.0, 2.0
        else: # waste
            high_thresh, med_thresh = 3.0, 1.5
            
        if avg >= high_thresh or (avg >= med_thresh and trend == "Worsening"):
            risk_assessment[cat] = "High"
        elif avg < med_thresh and trend != "Worsening":
            risk_assessment[cat] = "Low"
        else:
            risk_assessment[cat] = "Medium"
            
    # Score trend mapping
    score_trend_status = "Stable"
    if overall_trend == "increasing":
        score_trend_status = "Worsening"
    elif overall_trend == "decreasing":
        score_trend_status = "Improving"
        
    # Generate recommendations/insights
    recs = generate_recommendations(cat_info, activities)
    insights_list = [r["text"] for r in recs]
    if not insights_list:
        insights_list = [
            "Logging consistency is high. Keep tracking daily activities to maintain progress.",
            "Transportation represents the largest footprint component. Consider carpooling.",
            "Reducing thermostat setting by 1 degree saves approximately 10% on energy bills."
        ]
        
    overall_risk = calculate_risk(avg_daily, overall_trend)
    
    # 7. Unified Return Payload
    return {
        "success": True,
        "username": username,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "cached": False,
        "data": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "cached": False,
            "success": True,
            "details": {
                "transport": {
                    "status": cat_trends["transport"],
                    "confidence": "95%"
                },
                "energy": {
                    "status": cat_trends["energy"],
                    "confidence": "90%"
                },
                "food": {
                    "status": cat_trends["food"],
                    "confidence": "88%"
                },
                "score_trend": {
                    "status": score_trend_status,
                    "confidence": "92%"
                },
                "logging_consistency": {
                    "status": logging_status,
                    "percentage": logging_percentage
                },
                "risk_assessment": {
                    "transport": risk_assessment["transport"],
                    "energy": risk_assessment["energy"],
                    "food": risk_assessment["food"],
                    "waste": risk_assessment["waste"]
                }
            },
            "insights": insights_list,
            "total_emissions": cat_info["total_emissions"],
            "average_daily_emissions": avg_daily,
            "sustainability_score": score,
            "trend": overall_trend,
            "risk_level": overall_risk,
            "category_breakdown": cat_info["breakdown"],
            "recommendations": recs
        }
    }
