def calculate_risk(avg_daily_emissions, trend):
    """
    Determines environmental impact risk level as 'low', 'medium', or 'high'
    based on average daily emissions and the calculated trend.
    
    Rules:
    - High risk: average daily emissions >= 12.0 kg CO2, OR (average >= 8.0 kg CO2 with an 'increasing' trend).
    - Low risk: average daily emissions < 5.0 kg CO2 and trend is not 'increasing'.
    - Medium risk: all other cases.
    """
    try:
        avg_val = float(avg_daily_emissions)
    except (ValueError, TypeError):
        avg_val = 0.0
        
    trend_val = str(trend).lower().strip()
    
    if avg_val >= 12.0 or (avg_val >= 8.0 and trend_val == "increasing"):
        return "high"
    elif avg_val < 5.0 and trend_val != "increasing":
        return "low"
    else:
        return "medium"
