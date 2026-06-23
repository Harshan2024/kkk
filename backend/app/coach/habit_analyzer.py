from typing import List, Dict, Any
from datetime import datetime
from app.coach.coach_models import (
    HabitPattern,
    EnergyHabit,
    FoodHabit,
    TransportHabit,
    WasteHabit
)

def analyze_habits(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyzes history records and extracts patterns, energy, food, transport, and waste profiles.
    """
    patterns = []
    
    # --- 1. Base Variables for analysis ---
    total_records = len(records)
    days_logged = set()
    for r in records:
        ts = r.get("timestamp", "")
        if ts:
            days_logged.add(ts[:10])
    num_days = max(1, len(days_logged))
    
    # --- 2. Energy Habit Analysis ---
    ac_total_hours = 0.0
    ac_total_carbon = 0.0
    energy_total_carbon = 0.0
    has_energy = False
    
    # --- 3. Food Habit Analysis ---
    meat_meals_count = 0
    veg_meals_count = 0
    has_food = False
    
    # --- 4. Transport Habit Analysis ---
    public_transport_km = 0.0
    private_transport_km = 0.0
    has_transport = False
    
    # --- 5. Waste Habit Analysis ---
    plastic_waste_kg = 0.0
    other_waste_kg = 0.0
    recycling_events = 0
    has_waste = False
    
    # Loop through all activities in all records
    for r in records:
        total_carbon = r.get("total_carbon", 0.0)
        activities = r.get("activities", [])
        
        for act in activities:
            name = act.get("name", "").lower()
            category = act.get("category", "").lower()
            quantity = float(act.get("quantity") or 0.0)
            carbon = float(act.get("carbon") or 0.0)
            
            # Energy Details
            if category in ["energy", "electricity", "appliances"]:
                has_energy = True
                energy_total_carbon += carbon
                if "ac" in name or "air conditioner" in name:
                    ac_total_hours += quantity
                    ac_total_carbon += carbon
                    
            # Food Details
            elif category == "food":
                has_food = True
                is_animal = any(term in name for term in ["chicken", "mutton", "biriyani", "biryani", "briyani", "egg", "meat", "fish", "pork", "beef"])
                if is_animal:
                    meat_meals_count += 1
                else:
                    veg_meals_count += 1
                    
            # Transport Details
            elif category == "transport":
                has_transport = True
                is_public = any(term in name for term in ["train", "bus", "metro", "subway", "tram", "public", "cycle", "cycling", "walk", "walking", "run", "running"])
                if is_public:
                    public_transport_km += quantity
                else:
                    private_transport_km += quantity
                    
            # Waste Details
            elif category == "waste":
                has_waste = True
                if "plastic" in name:
                    plastic_waste_kg += quantity
                else:
                    other_waste_kg += quantity
                if "recycle" in name or "recycling" in name:
                    recycling_events += 1

    # --- Energy Report Calculations ---
    avg_ac_hours_per_day = ac_total_hours / num_days
    ac_percent_energy_emissions = (ac_total_carbon / energy_total_carbon * 100.0) if energy_total_carbon > 0 else 0.0
    
    if has_energy:
        if avg_ac_hours_per_day > 4.0:
            energy_finding = f"AC usage is high ({avg_ac_hours_per_day:.1f} hours/day). AC contributes {ac_percent_energy_emissions:.1f}% of energy emissions."
            patterns.append(HabitPattern(pattern="high_ac_usage", confidence=0.96, category="energy"))
        else:
            energy_finding = f"AC contributes {ac_percent_energy_emissions:.1f}% of energy emissions"
    else:
        energy_finding = ""
        
    energy_habit = EnergyHabit(
        finding=energy_finding,
        ac_hours=avg_ac_hours_per_day,
        ac_percentage=ac_percent_energy_emissions
    )
    
    # --- Food Report Calculations ---
    total_food_meals = meat_meals_count + veg_meals_count
    veg_ratio = (veg_meals_count / total_food_meals) if total_food_meals > 0 else 0.0
    animal_ratio = (meat_meals_count / total_food_meals) if total_food_meals > 0 else 0.0
    
    if has_food:
        if animal_ratio > 0.5:
            food_profile = "high_meat_consumption"
            patterns.append(HabitPattern(pattern="high_meat_intake", confidence=0.90, category="food"))
        elif veg_ratio > 0.8:
            food_profile = "plant_based_lean"
        else:
            food_profile = "balanced_diet"
        food_finding = f"Food profile is {food_profile.replace('_', ' ')}. Vegetarian ratio is {veg_ratio:.2f}."
    else:
        food_profile = ""
        food_finding = ""
        
    food_habit = FoodHabit(
        finding=food_finding,
        food_profile=food_profile,
        veg_ratio=round(veg_ratio, 2),
        animal_ratio=round(animal_ratio, 2)
    )
    
    # --- Transport Report Calculations ---
    total_km = public_transport_km + private_transport_km
    public_ratio = (public_transport_km / total_km) if total_km > 0 else 0.0
    
    if has_transport:
        if public_ratio > 0.5:
            transport_profile = "public_transport_user"
        else:
            transport_profile = "private_driver"
            patterns.append(HabitPattern(pattern="private_vehicle_dependency", confidence=0.88, category="transport"))
        transport_finding = f"Transport profile is {transport_profile.replace('_', ' ')}. Public transport ratio is {public_ratio:.2f}."
    else:
        transport_profile = ""
        transport_finding = ""
        
    transport_habit = TransportHabit(
        finding=transport_finding,
        transport_profile=transport_profile,
        public_transport_ratio=round(public_ratio, 2)
    )
    
    # --- Waste Report Calculations ---
    if has_waste:
        if plastic_waste_kg > other_waste_kg:
            waste_profile = "high_plastic_generation"
            patterns.append(HabitPattern(pattern="plastic_waste_heavy", confidence=0.85, category="waste"))
        else:
            waste_profile = "low_plastic_generation"
        waste_finding = f"Waste profile is {waste_profile.replace('_', ' ')}. Recycling frequency: {recycling_events}."
    else:
        waste_profile = ""
        waste_finding = ""
        
    waste_habit = WasteHabit(
        finding=waste_finding,
        waste_profile=waste_profile,
        recycling_frequency=recycling_events
    )
    
    return {
        "patterns": patterns,
        "energy": energy_habit,
        "food": food_habit,
        "transport": transport_habit,
        "waste": waste_habit
    }

def detect_achievements(records: List[Dict[str, Any]]) -> List[str]:
    """
    Detects achievement milestones based on user activity logs.
    """
    achievements = []
    if not records:
        return achievements
        
    # 1. Low Carbon Day (daily emission < 1.0 kg)
    daily_carbon = {}
    for r in records:
        ts = r.get("timestamp", "")[:10]
        daily_carbon[ts] = daily_carbon.get(ts, 0.0) + r.get("total_carbon", 0.0)
        
    has_low_carbon = any(val < 1.0 for val in daily_carbon.values())
    if has_low_carbon:
        achievements.append("low_carbon_day")
        
    # 2. Streaks (7-day and 30-day)
    sorted_days = sorted(list(daily_carbon.keys()))
    current_streak = 0
    max_streak = 0
    prev_date = None
    
    for day_str in sorted_days:
        curr_date = datetime.strptime(day_str, "%Y-%m-%d").date()
        if prev_date is None:
            current_streak = 1
        elif (curr_date - prev_date).days == 1:
            current_streak += 1
        elif (curr_date - prev_date).days > 1:
            current_streak = 1
        prev_date = curr_date
        if current_streak > max_streak:
            max_streak = current_streak
            
    if max_streak >= 30:
        achievements.append("30_day_streak")
    if max_streak >= 7:
        achievements.append("7_day_streak")
        
    # 3. Reduction Milestones (compared to a baseline average of 10.0kg per day)
    baseline_carbon_per_day = 10.0
    total_carbon = sum(r.get("total_carbon", 0.0) for r in records)
    num_days = max(1, len(daily_carbon))
    avg_carbon_per_day = total_carbon / num_days
    
    reduction = (baseline_carbon_per_day - avg_carbon_per_day) / baseline_carbon_per_day
    
    if reduction >= 0.50:
        achievements.append("50_percent_reduction")
    elif reduction >= 0.25:
        achievements.append("25_percent_reduction")
    elif reduction >= 0.10:
        achievements.append("10_percent_reduction")
        
    return achievements
