from typing import List, Dict, Any
from app.coach.coach_models import DayPlan, ActionPlan

def generate_recommendations(records: List[Dict[str, Any]]) -> List[str]:
    """
    Generates list of actionable recommendations based on carbon ratios.
    """
    category_carbon = {"food": 0.0, "transport": 0.0, "energy": 0.0, "waste": 0.0}
    total_carbon = 0.0
    
    for r in records:
        activities = r.get("activities", [])
        for act in activities:
            cat = act.get("category", "other").lower()
            carbon = float(act.get("carbon") or 0.0)
            
            if cat in ["electricity", "appliances", "energy"]:
                mapped_cat = "energy"
            elif cat in ["food", "transport", "waste"]:
                mapped_cat = cat
            else:
                mapped_cat = "energy"
                
            category_carbon[mapped_cat] = category_carbon.get(mapped_cat, 0.0) + carbon
            total_carbon += carbon
            
    recommendations = []
    
    if total_carbon > 0.0:
        food_pct = (category_carbon["food"] / total_carbon) * 100.0
        transport_pct = (category_carbon["transport"] / total_carbon) * 100.0
        energy_pct = (category_carbon["energy"] / total_carbon) * 100.0
        waste_pct = (category_carbon["waste"] / total_carbon) * 100.0
        
        if food_pct > 40.0:
            recommendations.append("Reduce meat meals by 2 servings/week")
        if transport_pct > 40.0:
            recommendations.append("Increase train or bus usage")
        if energy_pct > 35.0:
            recommendations.append("Reduce AC runtime")
        if waste_pct > 25.0:
            recommendations.append("Improve recycling habits")
            
    # Add default recommendation if list is empty
    if not recommendations:
        recommendations.append("Swap short driving trips with walking or cycling to build a healthy routine.")
        recommendations.append("Consider turning off air conditioning 1 hour earlier daily.")
        
    return recommendations

def generate_action_plan(records: List[Dict[str, Any]]) -> ActionPlan:
    """
    Generates a 7-day sustainability plan tailored to the user's highest emission category.
    """
    category_carbon = {"food": 0.0, "transport": 0.0, "energy": 0.0, "waste": 0.0}
    
    for r in records:
        activities = r.get("activities", [])
        for act in activities:
            cat = act.get("category", "other").lower()
            carbon = float(act.get("carbon") or 0.0)
            
            if cat in ["electricity", "appliances", "energy"]:
                mapped_cat = "energy"
            elif cat in ["food", "transport", "waste"]:
                mapped_cat = cat
            else:
                mapped_cat = "energy"
                
            category_carbon[mapped_cat] = category_carbon.get(mapped_cat, 0.0) + carbon

    highest_cat = max(category_carbon, key=category_carbon.get) if any(category_carbon.values()) else "default"
    
    plan = []
    if highest_cat == "energy":
        plan = [
            DayPlan(day=1, task="Set AC temperature to 24°C instead of 20°C"),
            DayPlan(day=2, task="Reduce AC active time by 1 hour today"),
            DayPlan(day=3, task="Unplug 3 idle appliances that draw standby power"),
            DayPlan(day=4, task="Charge your laptop only when battery is below 20%"),
            DayPlan(day=5, task="Use natural cooling or a fan during the night instead of AC"),
            DayPlan(day=6, task="Audit lightbulbs; ensure LED alternatives are in place"),
            DayPlan(day=7, task="Implement a strict 2-hour zero AC window in the evening")
        ]
    elif highest_cat == "food":
        plan = [
            DayPlan(day=1, task="Choose a completely vegetarian lunch"),
            DayPlan(day=2, task="Avoid animal-based takeouts (like Chicken Biriyani)"),
            DayPlan(day=3, task="Prepare a plant-based dinner with lentils or beans"),
            DayPlan(day=4, task="Buy seasonal local fruits for snack alternatives"),
            DayPlan(day=5, task="Minimize food waste by meal planning for the next 3 days"),
            DayPlan(day=6, task="Choose a dairy-free milk alternative (oat/soy) for coffee/tea"),
            DayPlan(day=7, task="Commit to a full plant-based day of eating")
        ]
    elif highest_cat == "transport":
        plan = [
            DayPlan(day=1, task="Walk or cycle for trips under 2 km"),
            DayPlan(day=2, task="Choose public transit (train or bus) for commutes"),
            DayPlan(day=3, task="Swap 1 car journey for cycling or walking"),
            DayPlan(day=4, task="Carpool with a friend or colleague for longer trips"),
            DayPlan(day=5, task="Use electric transit options where possible"),
            DayPlan(day=6, task="Complete 5,000 steps today instead of driving"),
            DayPlan(day=7, task="Establish a car-free day over the weekend")
        ]
    else: # Default or Waste
        plan = [
            DayPlan(day=1, task="Use train instead of bike"),
            DayPlan(day=2, task="Reduce AC usage by 1 hour"),
            DayPlan(day=3, task="Choose vegetarian meal"),
            DayPlan(day=4, task="Separate plastics and paper from trash bins"),
            DayPlan(day=5, task="Bring a reusable bottle and bag to avoid single-use plastics"),
            DayPlan(day=6, task="Turn off appliances completely when leaving rooms"),
            DayPlan(day=7, task="Recycle any electronic waste (old chargers, batteries)")
        ]
        
    return ActionPlan(plan=plan)
