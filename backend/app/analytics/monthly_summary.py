from datetime import datetime, date, timedelta

def get_val(obj, attr, default=None):
    if isinstance(obj, dict):
        return obj.get(attr, default)
    return getattr(obj, attr, default)

def calculate_monthly_summary(activities: list, ref_date: date = None) -> dict:
    """
    Calculates 30 Day Carbon Total and Average Daily Carbon.
    """
    if ref_date is None:
        ref_date = datetime.utcnow().date()
        
    start_date = ref_date - timedelta(days=29)
    
    monthly_total = 0.0
    for a in activities:
        logged_at = get_val(a, "logged_at")
        if isinstance(logged_at, str):
            try:
                logged_at = datetime.fromisoformat(logged_at.replace("Z", ""))
            except ValueError:
                continue
        if logged_at:
            a_date = logged_at.date()
            if start_date <= a_date <= ref_date:
                monthly_total += float(get_val(a, "calculated_value") or 0.0)
                
    daily_average = round(monthly_total / 30, 2)
    
    return {
        "monthly_total": round(monthly_total, 2),
        "daily_average": daily_average
    }
