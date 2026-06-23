def get_val(obj, attr, default=None):
    if isinstance(obj, dict):
        return obj.get(attr, default)
    return getattr(obj, attr, default)

def calculate_category_breakdown(activities: list) -> dict:
    """
    Calculates contribution percentages for the 4 core categories: transport, food, energy, waste.
    Validates that the percentages sum to exactly 100%.
    """
    transport_sum = 0.0
    food_sum = 0.0
    energy_sum = 0.0
    waste_sum = 0.0
    
    for a in activities:
        cat = str(get_val(a, "category", "")).strip().lower()
        val = float(get_val(a, "calculated_value") or 0.0)
        
        if cat == "transport":
            transport_sum += val
        elif cat == "food":
            food_sum += val
        elif cat in ("electricity", "appliances", "energy"):
            energy_sum += val
        elif cat == "waste":
            waste_sum += val
            
    sum_all_4 = transport_sum + food_sum + energy_sum + waste_sum
    
    if sum_all_4 > 0.0:
        transport_pct = int(round((transport_sum / sum_all_4) * 100))
        food_pct = int(round((food_sum / sum_all_4) * 100))
        energy_pct = int(round((energy_sum / sum_all_4) * 100))
        # Ensure exact 100% total by adjusting the remaining slice (waste)
        waste_pct = 100 - (transport_pct + food_pct + energy_pct)
    else:
        # Default zero distribution when there is no carbon data logged yet
        transport_pct = 0
        food_pct = 0
        energy_pct = 0
        waste_pct = 0
        
    return {
        "transport": transport_pct,
        "food": food_pct,
        "energy": energy_pct,
        "waste": waste_pct
    }
