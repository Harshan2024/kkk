def analyze_categories(activities):
    """
    Groups activities by category and returns the contribution percentage of each category.
    
    Supports both SQLAlchemy model instances and dictionaries.
    Categories mapped: 'transport', 'food', 'energy', 'waste', 'other'.
    """
    category_emissions = {
        "transport": 0.0,
        "food": 0.0,
        "energy": 0.0,
        "waste": 0.0,
        "other": 0.0
    }
    
    total_emissions = 0.0
    for act in activities:
        category = ""
        val = 0.0
        
        if hasattr(act, "category"):
            category = getattr(act, "category") or ""
            val = getattr(act, "calculated_value") or 0.0
        elif isinstance(act, dict):
            category = act.get("category") or ""
            val = act.get("calculated_value") or 0.0
        else:
            continue
            
        category = str(category).lower().strip()
        try:
            val = float(val)
        except (ValueError, TypeError):
            val = 0.0
        
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
            
        category_emissions[bucket] += val
        total_emissions += val
        
    percentages = {}
    if total_emissions > 0.0:
        for k, v in category_emissions.items():
            percentages[k] = round((v / total_emissions) * 100.0, 1)
    else:
        for k in category_emissions.keys():
            percentages[k] = 0.0
            
    return {
        "breakdown": percentages,
        "totals": {k: round(v, 2) for k, v in category_emissions.items()},
        "total_emissions": round(total_emissions, 2)
    }
