from typing import List, Dict, Any
from app.coach.coach_models import CoachInsight, ScoreExplanation

def generate_insights(records: List[Dict[str, Any]]) -> CoachInsight:
    """
    Generates CoachInsight details (top source, lowest source, best habit, worst habit, etc.).
    """
    if not records:
        return CoachInsight(
            top_source="N/A",
            contribution=0.0,
            lowest_source="N/A",
            best_habit="N/A",
            worst_habit="N/A",
            improvement_opportunity="N/A"
        )
        
    activity_carbon = {}
    activity_counts = {}
    total_all_carbon = 0.0
    
    # Calculate carbon sum for categories to identify best/worst habits
    category_carbon = {}
    
    for r in records:
        activities = r.get("activities", [])
        for act in activities:
            name = act.get("name", "Unknown")
            carbon = float(act.get("carbon") or 0.0)
            cat = act.get("category", "other").lower()
            
            activity_carbon[name] = activity_carbon.get(name, 0.0) + carbon
            activity_counts[name] = activity_counts.get(name, 0) + 1
            category_carbon[cat] = category_carbon.get(cat, 0.0) + carbon
            total_all_carbon += carbon

    if not activity_carbon:
        return CoachInsight(
            top_source="N/A",
            contribution=0.0,
            lowest_source="N/A",
            best_habit="N/A",
            worst_habit="N/A",
            improvement_opportunity="N/A"
        )

    # Sort activities by carbon emission
    sorted_activities = sorted(activity_carbon.items(), key=lambda x: x[1], reverse=True)
    top_source, top_carbon = sorted_activities[0]
    
    # Lowest source (greater than 0)
    non_zero_activities = [x for x in sorted_activities if x[1] > 0]
    if non_zero_activities:
        lowest_source, _ = non_zero_activities[-1]
    else:
        lowest_source = sorted_activities[-1][0]
        
    top_contribution = round((top_carbon / total_all_carbon * 100.0), 1) if total_all_carbon > 0 else 0.0
    
    # Determine best/worst habits and opportunities
    sorted_categories = sorted(category_carbon.items(), key=lambda x: x[1], reverse=True)
    highest_cat = sorted_categories[0][0] if sorted_categories else "food"
    lowest_cat = sorted_categories[-1][0] if sorted_categories else "waste"
    
    # Best Habit logic
    if lowest_cat == "transport":
        best_habit = "Choosing low-carbon public transport or active travel."
    elif lowest_cat == "food":
        best_habit = "Maintaining a low-impact, plant-centered food diet."
    elif lowest_cat == "energy":
        best_habit = "Conserving energy and keeping appliance runtimes low."
    else:
        best_habit = "Minimizing waste generation and keeping recycling high."
        
    # Worst Habit logic
    if highest_cat == "transport":
        worst_habit = "Frequent usage of high-emission private vehicles."
        improvement_opportunity = "Try swapping 2-3 short drives per week with walking, cycling, or public transit."
    elif highest_cat == "food":
        worst_habit = "High frequency of meat-based meals (such as Biriyani)."
        improvement_opportunity = "Introduce more plant-based alternatives and aim for at least 3-4 vegetarian days a week."
    elif highest_cat == "energy":
        worst_habit = "Excessive runtimes on heavy appliances like Air Conditioners."
        improvement_opportunity = "Set thermostat targets 1-2 degrees higher and reduce AC active time by 1-2 hours daily."
    else:
        worst_habit = "Generative patterns of non-recyclable plastic or electronics waste."
        improvement_opportunity = "Separate plastics, paper, and glass from landfill bags to improve recycling frequencies."

    return CoachInsight(
        top_source=top_source,
        contribution=top_contribution,
        lowest_source=lowest_source,
        best_habit=best_habit,
        worst_habit=worst_habit,
        improvement_opportunity=improvement_opportunity
    )

def explain_score(score: int, records: List[Dict[str, Any]]) -> ScoreExplanation:
    """
    Deconstructs a carbon score and lists category percentage contributions.
    """
    category_carbon = {"food": 0.0, "transport": 0.0, "energy": 0.0, "waste": 0.0}
    total_carbon = 0.0
    
    for r in records:
        activities = r.get("activities", [])
        for act in activities:
            cat = act.get("category", "other").lower()
            carbon = float(act.get("carbon") or 0.0)
            
            # Map standard categories
            if cat in ["electricity", "appliances", "energy"]:
                mapped_cat = "energy"
            elif cat in ["food", "transport", "waste"]:
                mapped_cat = cat
            else:
                mapped_cat = "energy" # Fallback to energy or another category
                
            category_carbon[mapped_cat] = category_carbon.get(mapped_cat, 0.0) + carbon
            total_carbon += carbon
            
    reasons = []
    if total_carbon > 0:
        for cat, carbon in category_carbon.items():
            pct = int(round(carbon / total_carbon * 100.0))
            if pct > 0:
                reasons.append(f"{cat.title()} emissions contribute {pct}%")
    else:
        reasons = [
            "Food emissions contribute 0%",
            "Transport contributes 0%",
            "Energy contributes 0%",
            "Waste contributes 0%"
        ]
        
    # Grade mappings
    if score >= 90:
        grade = "A+"
    elif score >= 80:
        grade = "A"
    elif score >= 70:
        grade = "B"
    elif score >= 60:
        grade = "C"
    else:
        grade = "D"
        
    return ScoreExplanation(
        score=score,
        grade=grade,
        reason=reasons
    )
