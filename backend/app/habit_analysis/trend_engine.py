from datetime import datetime, date

def calculate_trend(activities):
    """
    Groups activities by date and calculates the emission trend (increasing, decreasing, stable)
    by comparing the average emissions of the first half of tracking days vs the second half.
    
    A threshold of 0.5 kg CO2 difference is used to separate stable from increasing/decreasing.
    """
    if not activities:
        return "stable"
        
    daily_emissions = {}
    for act in activities:
        dt = None
        val = 0.0
        
        if hasattr(act, "logged_at"):
            dt_raw = getattr(act, "logged_at")
            if isinstance(dt_raw, (datetime, date)):
                dt = dt_raw if isinstance(dt_raw, date) else dt_raw.date()
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
            val = act.get("calculated_value") or 0.0
            
        if not dt:
            dt = date.today()
            
        try:
            val = float(val)
        except (ValueError, TypeError):
            val = 0.0
            
        daily_emissions[dt] = daily_emissions.get(dt, 0.0) + val
        
    sorted_dates = sorted(list(daily_emissions.keys()))
    
    if len(sorted_dates) < 2:
        return "stable"
        
    mid = len(sorted_dates) // 2
    first_half_dates = sorted_dates[:mid]
    second_half_dates = sorted_dates[mid:]
    
    avg_first = sum(daily_emissions[d] for d in first_half_dates) / len(first_half_dates)
    avg_second = sum(daily_emissions[d] for d in second_half_dates) / len(second_half_dates)
    
    diff = avg_second - avg_first
    
    if diff > 0.5:
        return "increasing"
    elif diff < -0.5:
        return "decreasing"
    else:
        return "stable"
