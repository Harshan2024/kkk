def generate_recommendations(category_breakdown: dict) -> list:
    """
    Scans category percentages and generates actionable suggestions.
    """
    recommendations = []

    transport_pct = category_breakdown.get("transport", 0)
    food_pct = category_breakdown.get("food", 0)
    energy_pct = category_breakdown.get("energy", 0)
    waste_pct = category_breakdown.get("waste", 0)

    if transport_pct > 35:
        recommendations.append("Use public transport more often.")
    if food_pct > 40:
        recommendations.append("Reduce high-carbon meat meals.")
    if energy_pct > 35:
        recommendations.append("Reduce AC usage duration.")
    if waste_pct > 25:
        recommendations.append("Improve recycling habits.")

    # Fallback/balanced suggestions if no high thresholds are met
    if not recommendations:
        recommendations.append("Your carbon footprint is well-balanced! Keep up the good work.")
        recommendations.append("Consider walking or cycling for short-distance trips.")

    return recommendations
