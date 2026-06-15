from sqlalchemy.orm import Session
from app.models import Category, EmissionFactor

# Define the standard categories to display in the UI
DEFAULT_CATEGORIES = [
    {"name": "food", "display_name": "Food & Diet", "icon": "Utensils"},
    {"name": "transport", "display_name": "Transport & Travel", "icon": "Car"},
    {"name": "electricity", "display_name": "Electricity", "icon": "Zap"},
    {"name": "appliances", "display_name": "Appliances", "icon": "Tv"},
    {"name": "shopping", "display_name": "Shopping & Goods", "icon": "ShoppingBag"},
    {"name": "waste", "display_name": "Waste Management", "icon": "Trash2"},
    {"name": "water", "display_name": "Water Usage", "icon": "Droplet"},
    {"name": "lifestyle", "display_name": "Lifestyle & Activities", "icon": "Activity"},
    {"name": "exercise", "display_name": "Exercise & Fitness", "icon": "Dumbbell"},
]

# Define standard emission factors with regional configurations
DEFAULT_EMISSION_FACTORS = [
    # --- FOOD (kgCO2e per kg) ---
    {"category": "food", "item_key": "beef", "display_name": "Beef", "factor": 60.0, "unit": "kg", "source": "Our World In Data", "region": "Global", "confidence": 0.92},
    {"category": "food", "item_key": "chicken", "display_name": "Chicken", "factor": 6.9, "unit": "kg", "source": "Our World In Data", "region": "Global", "confidence": 0.90},
    {"category": "food", "item_key": "rice", "display_name": "Rice", "factor": 2.7, "unit": "kg", "source": "IPCC", "region": "Global", "confidence": 0.88},
    {"category": "food", "item_key": "curd", "display_name": "Curd/Yogurt", "factor": 2.2, "unit": "kg", "source": "Climatiq", "region": "Global", "confidence": 0.85},
    {"category": "food", "item_key": "milk", "display_name": "Milk", "factor": 3.0, "unit": "kg", "source": "Our World In Data", "region": "Global", "confidence": 0.89},
    {"category": "food", "item_key": "egg", "display_name": "Egg", "factor": 4.5, "unit": "kg", "source": "DEFRA", "region": "Global", "confidence": 0.87},
    {"category": "food", "item_key": "vegetables", "display_name": "Vegetables", "factor": 0.5, "unit": "kg", "source": "IPCC", "region": "Global", "confidence": 0.80},
    {"category": "food", "item_key": "fish", "display_name": "Fish", "factor": 5.4, "unit": "kg", "source": "Our World In Data", "region": "Global", "confidence": 0.86},
    {"category": "food", "item_key": "cheese", "display_name": "Cheese", "factor": 21.0, "unit": "kg", "source": "Our World In Data", "region": "Global", "confidence": 0.89},
    {"category": "food", "item_key": "bread", "display_name": "Bread", "factor": 1.2, "unit": "kg", "source": "DEFRA", "region": "Global", "confidence": 0.82},
    {"category": "food", "item_key": "paneer", "display_name": "Paneer", "factor": 12.0, "unit": "kg", "source": "Climatiq", "region": "Global", "confidence": 0.83},
    
    # --- TRANSPORT (kgCO2e per km) ---
    {"category": "transport", "item_key": "petrol car", "display_name": "Petrol Car", "factor": 0.192, "unit": "km", "source": "DEFRA", "region": "Global", "confidence": 0.95},
    {"category": "transport", "item_key": "diesel car", "display_name": "Diesel Car", "factor": 0.171, "unit": "km", "source": "DEFRA", "region": "Global", "confidence": 0.94},
    {"category": "transport", "item_key": "ev", "display_name": "Electric Vehicle", "factor": 0.053, "unit": "km", "source": "EPA", "region": "Global", "confidence": 0.90},
    {"category": "transport", "item_key": "bike", "display_name": "Motorbike", "factor": 0.072, "unit": "km", "source": "DEFRA", "region": "Global", "confidence": 0.91},
    {"category": "transport", "item_key": "bus", "display_name": "Bus", "factor": 0.105, "unit": "km", "source": "DEFRA", "region": "Global", "confidence": 0.89},
    {"category": "transport", "item_key": "train", "display_name": "Train", "factor": 0.041, "unit": "km", "source": "DEFRA", "region": "Global", "confidence": 0.92},
    {"category": "transport", "item_key": "metro", "display_name": "Metro/Subway", "factor": 0.029, "unit": "km", "source": "UK GHG", "region": "Global", "confidence": 0.93},
    {"category": "transport", "item_key": "flight", "display_name": "Flight (Air Travel)", "factor": 0.255, "unit": "km", "source": "IPCC", "region": "Global", "confidence": 0.95},
    {"category": "transport", "item_key": "walking", "display_name": "Walking", "factor": 0.0, "unit": "km", "source": "Calculated", "region": "Global", "confidence": 0.99},
    {"category": "transport", "item_key": "cycling", "display_name": "Cycling", "factor": 0.0, "unit": "km", "source": "Calculated", "region": "Global", "confidence": 0.99},
    
    # --- Normalized spaCy Transport Factors ---
    {"category": "transport", "item_key": "electric_train", "display_name": "Electric Train", "factor": 0.020, "unit": "km", "source": "DEFRA", "region": "Global", "confidence": 0.92},
    {"category": "transport", "item_key": "electric_bus", "display_name": "Electric Bus", "factor": 0.060, "unit": "km", "source": "DEFRA", "region": "Global", "confidence": 0.89},
    {"category": "transport", "item_key": "electric_scooter", "display_name": "Electric Scooter", "factor": 0.015, "unit": "km", "source": "DEFRA", "region": "Global", "confidence": 0.91},
    {"category": "transport", "item_key": "electric_bike", "display_name": "Electric Bike", "factor": 0.020, "unit": "km", "source": "DEFRA", "region": "Global", "confidence": 0.91},
    {"category": "transport", "item_key": "petrol_car", "display_name": "Petrol Car (Normalized)", "factor": 0.192, "unit": "km", "source": "DEFRA", "region": "Global", "confidence": 0.95},
    {"category": "transport", "item_key": "diesel_car", "display_name": "Diesel Car (Normalized)", "factor": 0.171, "unit": "km", "source": "DEFRA", "region": "Global", "confidence": 0.94},
    {"category": "transport", "item_key": "hybrid_car", "display_name": "Hybrid Car", "factor": 0.095, "unit": "km", "source": "DEFRA", "region": "Global", "confidence": 0.93},
    {"category": "transport", "item_key": "cng_car", "display_name": "CNG Car", "factor": 0.110, "unit": "km", "source": "DEFRA", "region": "Global", "confidence": 0.92},
    {"category": "transport", "item_key": "auto_rickshaw", "display_name": "Auto Rickshaw", "factor": 0.090, "unit": "km", "source": "DEFRA", "region": "Global", "confidence": 0.91},
    
    # --- EXERCISE (0.0 kgCO2e per km/item) ---
    {"category": "exercise", "item_key": "running", "display_name": "Running", "factor": 0.0, "unit": "km", "source": "Calculated", "region": "Global", "confidence": 1.0},
    {"category": "exercise", "item_key": "walking", "display_name": "Walking", "factor": 0.0, "unit": "km", "source": "Calculated", "region": "Global", "confidence": 1.0},
    {"category": "exercise", "item_key": "jogging", "display_name": "Jogging", "factor": 0.0, "unit": "km", "source": "Calculated", "region": "Global", "confidence": 1.0},
    {"category": "exercise", "item_key": "cycling", "display_name": "Cycling", "factor": 0.0, "unit": "km", "source": "Calculated", "region": "Global", "confidence": 1.0},
    {"category": "exercise", "item_key": "swimming", "display_name": "Swimming", "factor": 0.0, "unit": "km", "source": "Calculated", "region": "Global", "confidence": 1.0},
    {"category": "exercise", "item_key": "exercise", "display_name": "Workout / Exercise", "factor": 0.0, "unit": "item", "source": "Calculated", "region": "Global", "confidence": 1.0},
    
    # --- REGIONAL GRID ELECTRICITY (kgCO2e per kWh) ---
    {"category": "electricity", "item_key": "grid electricity", "display_name": "Grid Electricity (Global)", "factor": 0.70, "unit": "kWh", "source": "IEA", "region": "Global", "confidence": 0.90},
    {"category": "electricity", "item_key": "grid electricity", "display_name": "Grid Electricity (India)", "factor": 0.82, "unit": "kWh", "source": "CEA", "region": "India", "country": "India", "confidence": 0.94},
    {"category": "electricity", "item_key": "grid electricity", "display_name": "Grid Electricity (USA)", "factor": 0.38, "unit": "kWh", "source": "EPA eGRID", "region": "USA", "country": "USA", "confidence": 0.96},
    {"category": "electricity", "item_key": "grid electricity", "display_name": "Grid Electricity (California)", "factor": 0.22, "unit": "kWh", "source": "CARB", "region": "California", "country": "USA", "state": "California", "confidence": 0.97},
    {"category": "electricity", "item_key": "grid electricity", "display_name": "Grid Electricity (Germany)", "factor": 0.40, "unit": "kWh", "source": "UBA", "region": "Germany", "country": "Germany", "confidence": 0.93},
    {"category": "electricity", "item_key": "grid electricity", "display_name": "Grid Electricity (France)", "factor": 0.06, "unit": "kWh", "source": "RTE", "region": "France", "country": "France", "confidence": 0.97},
    
    # --- RENEWABLES ---
    {"category": "electricity", "item_key": "solar electricity", "display_name": "Solar/Renewable", "factor": 0.02, "unit": "kWh", "source": "NREL", "region": "Global", "confidence": 0.91},

    # --- APPLIANCES (WATTAGE VALUES) ---
    {"category": "appliances", "item_key": "ac", "display_name": "Air Conditioner (1.5 Ton)", "factor": 1500.0, "unit": "W", "source": "Appliance Spec", "region": "Global", "confidence": 0.95},
    {"category": "appliances", "item_key": "fan", "display_name": "Ceiling Fan", "factor": 75.0, "unit": "W", "source": "Appliance Spec", "region": "Global", "confidence": 0.95},
    {"category": "appliances", "item_key": "refrigerator", "display_name": "Refrigerator", "factor": 100.0, "unit": "W", "source": "Appliance Spec", "region": "Global", "confidence": 0.95},
    {"category": "appliances", "item_key": "laptop", "display_name": "Laptop", "factor": 60.0, "unit": "W", "source": "Appliance Spec", "region": "Global", "confidence": 0.95},
    {"category": "appliances", "item_key": "tv", "display_name": "Television", "factor": 100.0, "unit": "W", "source": "Appliance Spec", "region": "Global", "confidence": 0.95},
    {"category": "appliances", "item_key": "washing machine", "display_name": "Washing Machine", "factor": 500.0, "unit": "W", "source": "Appliance Spec", "region": "Global", "confidence": 0.95},
    {"category": "appliances", "item_key": "water heater", "display_name": "Water Heater (Geyser)", "factor": 2000.0, "unit": "W", "source": "Appliance Spec", "region": "Global", "confidence": 0.95},
    {"category": "appliances", "item_key": "lights", "display_name": "LED Lights", "factor": 15.0, "unit": "W", "source": "Appliance Spec", "region": "Global", "confidence": 0.95},
    
    # --- SHOPPING (kgCO2e per item) ---
    {"category": "shopping", "item_key": "clothing", "display_name": "Clothing Item", "factor": 6.0, "unit": "item", "source": "UNEP", "region": "Global", "confidence": 0.85},
    {"category": "shopping", "item_key": "shoes", "display_name": "Pair of Shoes", "factor": 15.0, "unit": "item", "source": "Quantis", "region": "Global", "confidence": 0.80},
    {"category": "shopping", "item_key": "electronics", "display_name": "Smartphone / Tablet", "factor": 80.0, "unit": "item", "source": "Apple Reports", "region": "Global", "confidence": 0.90},
    
    # --- WASTE (kgCO2e per kg) ---
    {"category": "waste", "item_key": "organic waste", "display_name": "Organic/Food Waste", "factor": 0.5, "unit": "kg", "source": "EPA", "region": "Global", "confidence": 0.85},
    {"category": "waste", "item_key": "plastic waste", "display_name": "Plastic Waste", "factor": 2.0, "unit": "kg", "source": "Climatiq", "region": "Global", "confidence": 0.88},
    {"category": "waste", "item_key": "paper waste", "display_name": "Paper/Cardboard Waste", "factor": 1.0, "unit": "kg", "source": "EPA", "region": "Global", "confidence": 0.87},
    {"category": "waste", "item_key": "recycling", "display_name": "Sorted Recyclables", "factor": 0.1, "unit": "kg", "source": "Calculated", "region": "Global", "confidence": 0.90},
    
    # --- WATER (kgCO2e per Litre) ---
    {"category": "water", "item_key": "tap water", "display_name": "Tap Water", "factor": 0.0003, "unit": "L", "source": "DEFRA", "region": "Global", "confidence": 0.91},
]

# Quick conversion mapping for food items/dishes to weight in kilograms
FOOD_UNIT_TO_KG = {
    "plate curd rice": 0.350,
    "curd rice": 0.350,
    "plate rice": 0.300,
    "bowl rice": 0.200,
    "rice": 0.300,
    "chicken biryani": 0.450,
    "plate chicken biryani": 0.450,
    "biryani": 0.450,
    "bowl curry": 0.200,
    "curry": 0.200,
    "cup milk": 0.240,
    "glass milk": 0.240,
    "milk": 0.240,
    "dosa": 0.120,
    "idli": 0.040,
    "plate vegetables": 0.250,
    "bowl vegetables": 0.150,
    "egg": 0.060,
}

def seed_db(db: Session):
    """
    Seeds categories and emission factors into the database.
    """
    # 1. Seed Categories
    for cat_data in DEFAULT_CATEGORIES:
        existing = db.query(Category).filter(Category.name == cat_data["name"]).first()
        if not existing:
            cat = Category(**cat_data)
            db.add(cat)
    
    # 2. Seed Emission Factors (supporting duplicate item_keys for different regions)
    for factor_data in DEFAULT_EMISSION_FACTORS:
        region = factor_data.get("region", "Global")
        existing = db.query(EmissionFactor).filter(
            EmissionFactor.item_key == factor_data["item_key"],
            EmissionFactor.region == region
        ).first()
        
        if not existing:
            factor = EmissionFactor(**factor_data)
            db.add(factor)
        else:
            # Update attributes if existing
            existing.factor = factor_data["factor"]
            existing.display_name = factor_data["display_name"]
            existing.unit = factor_data["unit"]
            existing.category = factor_data["category"]
            existing.source = factor_data.get("source", existing.source)
            existing.confidence = factor_data.get("confidence", existing.confidence)
            existing.country = factor_data.get("country", existing.country)
            existing.state = factor_data.get("state", existing.state)
            
    db.commit()
