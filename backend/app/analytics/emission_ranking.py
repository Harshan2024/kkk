def get_val(obj, attr, default=None):
    if isinstance(obj, dict):
        return obj.get(attr, default)
    return getattr(obj, attr, default)

def calculate_emission_ranking(activities: list) -> dict:
    """
    Identifies top 5 highest, top 5 lowest, and top 5 most frequent activities.
    """
    grouped = {}
    for a in activities:
        item = str(get_val(a, "item") or "Unknown")
        # Canonical names mapping
        from app.api.endpoints import canonical_display
        item_display = canonical_display(item)
        
        val = float(get_val(a, "calculated_value") or 0.0)
        
        if item_display not in grouped:
            grouped[item_display] = {"carbon": 0.0, "count": 0}
        grouped[item_display]["carbon"] += val
        grouped[item_display]["count"] += 1
        
    sorted_highest = sorted(grouped.items(), key=lambda x: x[1]["carbon"], reverse=True)
    sorted_lowest = sorted(grouped.items(), key=lambda x: x[1]["carbon"], reverse=False)
    sorted_frequent = sorted(grouped.items(), key=lambda x: x[1]["count"], reverse=True)
    
    top_sources = [{"activity": k, "carbon": round(v["carbon"], 2)} for k, v in sorted_highest[:5]]
    bottom_sources = [{"activity": k, "carbon": round(v["carbon"], 2)} for k, v in sorted_lowest[:5]]
    most_frequent = [{"activity": k, "count": v["count"]} for k, v in sorted_frequent[:5]]
    
    return {
        "top_sources": top_sources,
        "bottom_sources": bottom_sources,
        "most_frequent": most_frequent
    }
