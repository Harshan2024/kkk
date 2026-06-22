def get_val(obj, attr, default=None):
    if isinstance(obj, dict):
        return obj.get(attr, default)
    return getattr(obj, attr, default)

def calculate_sustainability_score(activities: list, daily_average: float, category_breakdown: dict) -> dict:
    """
    Compiles a composite 0-100 sustainability score and returns a letter grade.
    Weights: Starts at 100, deducts based on average daily carbon (threshold > 5.0 kg),
    high transport usage (> 35%), high food usage (> 40%), and high energy (> 35%).
    Adds bonus points (+5) for carbon-reducing or eco-friendly activities (recycled waste, walking/running/cycling).
    """
    score = 100.0

    # 1. Deduct for average daily carbon > 5.0 kg
    if daily_average > 5.0:
        # Deduct 5 points per kg above 5.0, capped at 50 points deduction
        deduction = (daily_average - 5.0) * 5.0
        score -= min(deduction, 50.0)

    # 2. Deduct for high category percentages
    transport_pct = category_breakdown.get("transport", 0)
    food_pct = category_breakdown.get("food", 0)
    energy_pct = category_breakdown.get("energy", 0)

    if transport_pct > 35:
        score -= 10.0
    if food_pct > 40:
        score -= 10.0
    if energy_pct > 35:
        score -= 10.0

    # 3. Add bonus points (+5) for eco-friendly or carbon-reducing activities
    has_bonus = False
    for a in activities:
        item = str(get_val(a, "item") or "").lower()
        cat = str(get_val(a, "category") or "").lower()
        if "walk" in item or "run" in item or "cycl" in item or "recycl" in item or (cat == "waste" and "recycl" in item):
            has_bonus = True
            break

    if has_bonus:
        score += 5.0

    # Ensure constraints [0, 100]
    score = max(0.0, min(100.0, score))
    rounded_score = int(round(score))

    # Grade mappings
    if rounded_score >= 90:
        grade = "A+"
    elif rounded_score >= 80:
        grade = "A"
    elif rounded_score >= 70:
        grade = "B"
    elif rounded_score >= 60:
        grade = "C"
    else:
        grade = "D"

    return {
        "score": rounded_score,
        "grade": grade
    }
