from datetime import datetime, date, timedelta

def get_val(obj, attr, default=None):
    if isinstance(obj, dict):
        return obj.get(attr, default)
    return getattr(obj, attr, default)

def calculate_weekly_summary(activities: list, ref_date: date = None) -> dict:
    """
    Calculates 7 Day Carbon Total, Average Daily Carbon, Highest Emission Day, Lowest Emission Day.
    """
    if ref_date is None:
        ref_date = datetime.utcnow().date()
        
    start_date = ref_date - timedelta(days=6)
    
    # Pre-populate all 7 days in range
    daily_emissions = {start_date + timedelta(days=i): 0.0 for i in range(7)}
    daily_counts = {start_date + timedelta(days=i): 0 for i in range(7)}
    
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
                daily_emissions[a_date] = daily_emissions.get(a_date, 0.0) + float(get_val(a, "calculated_value") or 0.0)
                daily_counts[a_date] = daily_counts.get(a_date, 0) + 1
                
    weekly_total = sum(daily_emissions.values())
    daily_average = round(weekly_total / 7, 2)
    
    highest_day = ""
    highest_emission = -1.0
    
    # Evaluate day names deterministically by sorting by date
    for d in sorted(daily_emissions.keys()):
        em = daily_emissions[d]
        d_name = d.strftime("%A")
        if em >= highest_emission:
            highest_emission = em
            highest_day = d_name
            
    if highest_emission < 0.0:
        highest_emission = 0.0
        highest_day = ref_date.strftime("%A")
        
    return {
        "weekly_total": round(weekly_total, 2),
        "daily_average": daily_average,
        "highest_day": highest_day,
        "highest_emission": round(highest_emission, 2)
    }
