from datetime import datetime, date, timedelta
from app.analytics.daily_summary import calculate_daily_summary
from app.analytics.weekly_summary import calculate_weekly_summary
from app.analytics.monthly_summary import calculate_monthly_summary
from app.analytics.category_breakdown import calculate_category_breakdown
from app.analytics.emission_ranking import calculate_emission_ranking
from app.analytics.sustainability_score import calculate_sustainability_score
from app.analytics.recommendation_engine import generate_recommendations

def get_val(obj, attr, default=None):
    if isinstance(obj, dict):
        return obj.get(attr, default)
    return getattr(obj, attr, default)

def get_activities_in_range(activities: list, start_date: date, end_date: date) -> list:
    filtered = []
    for a in activities:
        logged_at = get_val(a, "logged_at")
        if isinstance(logged_at, str):
            try:
                logged_at = datetime.fromisoformat(logged_at.replace("Z", ""))
            except ValueError:
                continue
        if logged_at:
            a_date = logged_at.date()
            if start_date <= a_date <= end_date:
                filtered.append(a)
    return filtered

def calculate_trend(current: float, previous: float) -> tuple:
    if previous == 0.0:
        if current > 0.0:
            return 100.0, "increasing"
        elif current == 0.0:
            return 0.0, "stable"
        else:
            return -100.0, "decreasing"
    
    change_pct = ((current - previous) / previous) * 100.0
    
    if change_pct > 1.0:
        status = "increasing"
    elif change_pct < -1.0:
        status = "decreasing"
    else:
        status = "stable"
        
    return round(change_pct, 1), status

def generate_analytics_payload(activities: list, ref_date: date = None) -> dict:
    """
    Orchestrates daily, weekly, monthly summaries, breakdown, rankings, sustainability grade,
    recommendations, and computes change trends.
    """
    if ref_date is None:
        ref_date = datetime.utcnow().date()
        
    # 1. Base Summaries
    daily_sum = calculate_daily_summary(activities, ref_date)
    weekly_sum = calculate_weekly_summary(activities, ref_date)
    monthly_sum = calculate_monthly_summary(activities, ref_date)
    
    # Filter activities for last 30 days for Breakdown, Rankings, Sustainability Score
    start_date_30d = ref_date - timedelta(days=29)
    activities_30d = get_activities_in_range(activities, start_date_30d, ref_date)
    
    category_breakdown = calculate_category_breakdown(activities_30d)
    rankings = calculate_emission_ranking(activities_30d)
    sustainability = calculate_sustainability_score(activities_30d, monthly_sum["daily_average"], category_breakdown)
    recommendations = generate_recommendations(category_breakdown)
    
    # 2. Trend Calculations
    # Daily: Today vs Yesterday
    yesterday = ref_date - timedelta(days=1)
    yesterday_total = sum(float(get_val(a, "calculated_value") or 0.0) for a in get_activities_in_range(activities, yesterday, yesterday))
    daily_trend_val, daily_trend_status = calculate_trend(daily_sum["total_carbon"], yesterday_total)
    
    daily_sum["trend_value"] = daily_trend_val
    daily_sum["trend_status"] = daily_trend_status
    
    # Weekly: Last 7 days vs Prior 7 days
    prev_weekly_start = ref_date - timedelta(days=13)
    prev_weekly_end = ref_date - timedelta(days=7)
    prev_weekly_total = sum(float(get_val(a, "calculated_value") or 0.0) for a in get_activities_in_range(activities, prev_weekly_start, prev_weekly_end))
    weekly_trend_val, weekly_trend_status = calculate_trend(weekly_sum["weekly_total"], prev_weekly_total)
    
    weekly_sum["trend_value"] = weekly_trend_val
    weekly_sum["trend_status"] = weekly_trend_status
    
    # Monthly: Last 30 days vs Prior 30 days
    prev_monthly_start = ref_date - timedelta(days=59)
    prev_monthly_end = ref_date - timedelta(days=30)
    prev_monthly_total = sum(float(get_val(a, "calculated_value") or 0.0) for a in get_activities_in_range(activities, prev_monthly_start, prev_monthly_end))
    monthly_trend_val, monthly_trend_status = calculate_trend(monthly_sum["monthly_total"], prev_monthly_total)
    
    monthly_sum["trend_value"] = monthly_trend_val
    monthly_sum["trend_status"] = monthly_trend_status
    
    return {
        "daily": daily_sum,
        "weekly": weekly_sum,
        "monthly": monthly_sum,
        "category_breakdown": category_breakdown,
        "rankings": rankings,
        "sustainability": sustainability,
        "recommendations": recommendations
    }
