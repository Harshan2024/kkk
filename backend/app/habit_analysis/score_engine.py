from datetime import datetime, date

def calculate_sustainability_score(activities):
    """
    Groups activities by date, calculates total daily emissions,
    finds the average daily emissions, and maps it to a 0-100 score.
    
    Budget:
      <= 3.0 kgCO2e -> 100 points
      >= 15.0 kgCO2e -> 0 points
      Else -> 100.0 - ((avg_emissions - 3.0) / 12.0) * 100.0
    """
    if not activities:
        return {
            "score": 96.0,
            "average_daily_emissions": 0.0,
            "days_tracked": 0
        }
        
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
                    # Fallback parser for other formats
                    try:
                        dt = datetime.strptime(dt_raw[:10], "%Y-%m-%d").date()
                    except Exception:
                        pass
            elif isinstance(dt_raw, (datetime, date)):
                dt = dt_raw if isinstance(dt_raw, date) else dt_raw.date()
            val = act.get("calculated_value") or 0.0
            
        if not dt:
            # Fallback to date.today() if no date parsed
            dt = date.today()
            
        try:
            val = float(val)
        except (ValueError, TypeError):
            val = 0.0
            
        daily_emissions[dt] = daily_emissions.get(dt, 0.0) + val
        
    if not daily_emissions:
        return {
            "score": 96.0,
            "average_daily_emissions": 0.0,
            "days_tracked": 0
        }
        
    avg_emissions = sum(daily_emissions.values()) / len(daily_emissions)
    
    if avg_emissions <= 3.0:
        score = 100.0
    elif avg_emissions >= 15.0:
        score = 0.0
    else:
        score = 100.0 - ((avg_emissions - 3.0) / 12.0) * 100.0
        
    return {
        "score": round(score, 1),
        "average_daily_emissions": round(avg_emissions, 2),
        "days_tracked": len(daily_emissions)
    }
