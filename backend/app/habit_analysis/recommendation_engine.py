def generate_recommendations(category_percentages, activities):
    """
    Generates personalized recommendations based on category breakdown
    and specific high-impact items in the user's activity log.
    
    Returns a list of dictionaries with recommendation details.
    """
    recs = []
    
    breakdown = category_percentages.get("breakdown", {})
    totals = category_percentages.get("totals", {})
    
    # Sort categories by footprint percentage to address highest impact first
    sorted_categories = sorted(
        [k for k in breakdown.keys() if k != "other"],
        key=lambda x: breakdown.get(x, 0.0),
        reverse=True
    )
    
    # Scan activities for specific items
    has_meat = False
    has_car = False
    has_ac = False
    has_plastic = False
    
    for act in activities:
        item = ""
        if hasattr(act, "item"):
            item = getattr(act, "item") or ""
        elif isinstance(act, dict):
            item = act.get("item") or ""
        item = str(item).lower()
        
        if any(w in item for w in ["biriyani", "chicken", "mutton", "beef", "meat", "rice"]):
            has_meat = True
        if any(w in item for w in ["car", "suv", "petrol", "diesel", "drive", "driving"]):
            has_car = True
        if any(w in item for w in ["ac", "air conditioner", "heater", "electricity"]):
            has_ac = True
        if any(w in item for w in ["plastic", "bottle", "e-waste", "electronic"]):
            has_plastic = True
            
    # Generate recommendations based on priorities
    for cat in sorted_categories:
        pct = breakdown.get(cat, 0.0)
        if pct < 5.0:
            continue  # Skip low-impact categories
            
        if cat == "transport":
            if has_car:
                recs.append({
                    "category": "transport",
                    "text": f"Your transportation contributes {pct}% of emissions. Swapping driving for cycling/walking or public transit can save substantial carbon.",
                    "potential_saving": 3.5,
                    "difficulty": "MEDIUM"
                })
            else:
                recs.append({
                    "category": "transport",
                    "text": "Optimize transit. Avoid single-passenger trips and try carpooling or public transit when possible.",
                    "potential_saving": 1.5,
                    "difficulty": "EASY"
                })
                
        elif cat == "food":
            if has_meat:
                recs.append({
                    "category": "food",
                    "text": f"Food choices account for {pct}% of your footprint. Chicken and mutton biriyani have high carbon intensity. Swapping two meat meals for plant-based alternatives will make a major difference.",
                    "potential_saving": 2.8,
                    "difficulty": "EASY"
                })
            else:
                recs.append({
                    "category": "food",
                    "text": "Reduce food waste. Properly planning weekly grocery trips and composting organic scraps avoids landfill methane release.",
                    "potential_saving": 0.8,
                    "difficulty": "EASY"
                })
                
        elif cat == "energy":
            if has_ac:
                recs.append({
                    "category": "energy",
                    "text": f"Energy usage is {pct}% of your footprint. Adjusting AC runtime down by 1 hour daily or raising target temp to 24°C saves energy.",
                    "potential_saving": 1.2,
                    "difficulty": "EASY"
                })
            else:
                recs.append({
                    "category": "energy",
                    "text": "Target phantom loads. Unplug idle appliances like chargers, TV setups, and microwaves when they are not in active use.",
                    "potential_saving": 0.4,
                    "difficulty": "EASY"
                })
                
        elif cat == "waste":
            if has_plastic:
                recs.append({
                    "category": "waste",
                    "text": f"Waste is responsible for {pct}% of emissions. Carry reusable bags/bottles and recycle plastic, cardboard, and metals to achieve zero-plastic milestones.",
                    "potential_saving": 0.6,
                    "difficulty": "EASY"
                })
            else:
                recs.append({
                    "category": "waste",
                    "text": "Start sorting recyclable waste at home. Keep paper/cardboard dry and recycle glass/metal containers.",
                    "potential_saving": 0.5,
                    "difficulty": "EASY"
                })
                
    # Fallback recommendations if list is too short
    if len(recs) < 3:
        recs.append({
            "category": "lifestyle",
            "text": "Track your footprint consistently to identify carbon trends and uncover micro-saving opportunities.",
            "potential_saving": 0.2,
            "difficulty": "EASY"
        })
        recs.append({
            "category": "appliances",
            "text": "Turn off lights when leaving a room and utilize natural light during daytime hours.",
            "potential_saving": 0.3,
            "difficulty": "EASY"
        })
        
    return recs[:4]  # Return top 3-4 recommendations
