from datetime import datetime, date

def get_val(obj, attr, default=None):
    if isinstance(obj, dict):
        return obj.get(attr, default)
    return getattr(obj, attr, default)

def calculate_daily_summary(activities: list, ref_date: date = None) -> dict:
    """
    Calculates today's total carbon, today's activities count,
    highest carbon activity, lowest carbon activity, average carbon per activity.
    """
    if ref_date is None:
        ref_date = datetime.utcnow().date()
        
    today_activities = []
    for a in activities:
        logged_at = get_val(a, "logged_at")
        if isinstance(logged_at, str):
            try:
                logged_at = datetime.fromisoformat(logged_at.replace("Z", ""))
            except ValueError:
                continue
        if logged_at and logged_at.date() == ref_date:
            today_activities.append(a)
            
    count = len(today_activities)
    total_carbon = sum(float(get_val(a, "calculated_value") or 0.0) for a in today_activities)
    average = round(total_carbon / count, 2) if count > 0 else 0.0
    
    highest_activity = ""
    highest_carbon = 0.0
    
    for a in today_activities:
        carb = float(get_val(a, "calculated_value") or 0.0)
        item = str(get_val(a, "item") or "")
        if carb >= highest_carbon:
            highest_carbon = carb
            highest_activity = item
            
    return {
        "date": "today",
        "activities": count,
        "total_carbon": round(total_carbon, 2),
        "average": average,
        "highest_activity": highest_activity,
        "highest_carbon": round(highest_carbon, 2)
    }
