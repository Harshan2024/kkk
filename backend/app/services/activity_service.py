from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Activity, User, SustainabilityScore, Achievement
from app.nlp.parser import parse_activity_text
from app.calculations.engines import (
    calculate_food_emission,
    calculate_transport_emission,
    calculate_appliance_emission,
    calculate_generic_emission
)

def get_or_create_user(db: Session, username: str = "demo_user") -> User:
    """
    Retrieves or creates a guest/demo user.
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        user = User(username=username)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def calculate_emissions(db: Session, parsed: dict, region: str = "Global") -> tuple[float, dict]:
    """
    Directs parsed activity data to correct calculation engine.
    """
    category = parsed.get("category") or "general"
    item = parsed.get("item") or "unknown"
    quantity = parsed.get("quantity") if parsed.get("quantity") is not None else 1.0
    unit = parsed.get("unit") or "unit"
    
    if category == "food":
        return calculate_food_emission(db, item, quantity, unit, region=region)
    elif category == "transport":
        return calculate_transport_emission(db, item, quantity, unit, region=region)
    elif category == "appliances" or category == "electricity":
        duration = quantity if unit == "hours" else 1.0
        qty = 1.0 if unit == "hours" else quantity
        return calculate_appliance_emission(db, item, duration, qty, region=region)
    else:
        return calculate_generic_emission(db, category, item, quantity, unit, region=region)

def log_activity(db: Session, username: str, text: str, region: str = "Global") -> Activity:
    """
    Parses, calculates emissions, saves to DB, updates daily score, and unlocks achievements.
    """
    # 1. Get user
    user = get_or_create_user(db, username)
    
    # 2. Parse text
    parsed = parse_activity_text(text)
    
    # 3. Calculate carbon
    emissions, metadata = calculate_emissions(db, parsed, region=region)
    
    # 4. Create activity record
    activity = Activity(
        user_id=user.id,
        input_text=text,
        category=parsed["category"],
        item=parsed["item"],
        quantity=parsed["quantity"],
        unit=parsed["unit"],
        calculated_value=emissions,
        metadata_json=metadata,
        region=region,
        logged_at=datetime.utcnow()
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    
    # 5. Update daily sustainability score
    update_daily_score(db, user.id, date.today())
    
    # 6. Check for achievements
    check_achievements(db, user.id, activity)
    
    return activity

def update_daily_score(db: Session, user_id: int, target_date: date) -> SustainabilityScore:
    """
    Calculates cumulative emissions for a day and maps it to a score from 0-100.
    Budget:
      <= 3.0 kgCO2e -> 100 points
      <= 15.0 kgCO2e -> Linear decrease
      > 15.0 kgCO2e -> 0 points
    """
    # Sum daily emissions
    start_time = datetime.combine(target_date, datetime.min.time())
    end_time = datetime.combine(target_date, datetime.max.time())
    
    daily_emissions = db.query(func.sum(Activity.calculated_value)).filter(
        Activity.user_id == user_id,
        Activity.logged_at >= start_time,
        Activity.logged_at <= end_time
    ).scalar() or 0.0
    
    # Calculate score
    if daily_emissions <= 3.0:
        score = 100.0
    elif daily_emissions >= 15.0:
        score = 0.0
    else:
        # Scale between 3.0 and 15.0
        score = 100.0 - ((daily_emissions - 3.0) / 12.0) * 100.0
        
    score_record = db.query(SustainabilityScore).filter(
        SustainabilityScore.user_id == user_id,
        SustainabilityScore.date == target_date
    ).first()
    
    if not score_record:
        score_record = SustainabilityScore(
            user_id=user_id,
            date=target_date,
            total_emissions=daily_emissions,
            score=score
        )
        db.add(score_record)
    else:
        score_record.total_emissions = daily_emissions
        score_record.score = score
        
    db.commit()
    db.refresh(score_record)
    return score_record

def check_achievements(db: Session, user_id: int, new_activity: Activity) -> list[Achievement]:
    """
    Checks triggers to unlock badges for sustainable habits.
    """
    unlocked = []
    
    def unlock(name: str, desc: str, badge_type: str):
        existing = db.query(Achievement).filter(
            Achievement.user_id == user_id,
            Achievement.name == name
        ).first()
        if not existing:
            ach = Achievement(
                user_id=user_id,
                name=name,
                description=desc,
                badge_type=badge_type
            )
            db.add(ach)
            unlocked.append(ach)
            
    # Trigger 1: First Log
    total_logs = db.query(Activity).filter(Activity.user_id == user_id).count()
    if total_logs >= 1:
        unlock("Eco Pioneer", "Logged your first carbon activity!", "bronze")
        
    # Trigger 2: Low Carbon Commuter (walk, cycle, metro, train)
    if new_activity.category == "transport" and new_activity.item in ["walking", "cycling", "metro", "train"]:
        unlock("Green Commuter", "Opted for low-emission transport (walk, cycle, metro or train).", "silver")
        
    # Trigger 3: Plant-Based Meal
    if new_activity.category == "food" and new_activity.item in ["curd rice", "vegetables", "dosa", "idli"]:
        unlock("Plant-based Champion", "Ate a carbon-conscious vegetarian or vegan meal.", "silver")
        
    # Trigger 4: Power Saver (solar energy or smart appliance duration)
    if new_activity.category == "appliances" and new_activity.quantity <= 1.0 and new_activity.unit == "hours":
        unlock("Power Saver", "Used energy-demanding appliances for 1 hour or less.", "bronze")
        
    # Trigger 5: Clean Streak (logged 5 activities in general)
    if total_logs >= 5:
        unlock("Consistent Climateer", "Logged 5 or more activities in CarbonTracker.", "gold")
        
    if unlocked:
        db.commit()
        
    return unlocked
