from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models import EmissionFactor
from app.emissions.factors import FOOD_UNIT_TO_KG, DEFAULT_EMISSION_FACTORS

from app.carbon.transport_factors import TRANSPORT_FACTORS
from app.carbon.transport_formula import calculate_transport_co2
from app.carbon.food_factors import FOOD_FACTORS
from app.carbon.food_formula import calculate_food_co2
from app.carbon.appliance_factors import APPLIANCE_WATTS, GRID_FACTORS
from app.carbon.appliance_formula import calculate_appliance_co2
from app.carbon.waste_factors import WASTE_FACTORS
from app.carbon.waste_formula import calculate_waste_co2
from app.carbon.shopping_factors import SHOPPING_FACTORS
from app.carbon.shopping_formula import calculate_shopping_co2


class CachedEmissionFactor:
    def __init__(self, category: str, item_key: str, display_name: str, factor: float, unit: str, region: str, source: str):
        self.category = category
        self.item_key = item_key
        self.display_name = display_name
        self.factor = factor
        self.unit = unit
        self.region = region
        self.source = source

_FACTOR_CACHE = {}
_ALL_FACTORS_CACHE = {}

# Database error resilient query helpers
def get_factor_first(db: Session, category: str = None, item_key: str = None, region: str = "Global") -> Any:
    """
    Queries an emission factor, matching region first.
    Falls back to 'Global' if region-specific entry does not exist.
    Falls back to local static config if the database connection fails.
    Caches results in memory to avoid repeated DB roundtrips.
    """
    cache_key = (category, item_key, region)
    if cache_key in _FACTOR_CACHE:
        return _FACTOR_CACHE[cache_key]
        
    record = None
    
    # Check if item_key is obviously unknown to avoid querying/timeout
    item_key_clean = item_key.lower().strip() if item_key else ""
    if not item_key or "unknown" in item_key_clean or item_key_clean == "general activity":
        _FACTOR_CACHE[cache_key] = None
        return None

    # Check if database is offline or degraded
    from app.database import session as db_session
    from app.database.session import check_database_health_throttled
    
    if db_session.OFFLINE_MODE or db_session.READ_ONLY_MODE or not check_database_health_throttled():
        # Bypass DB query entirely
        pass
    else:
        try:
            query = db.query(EmissionFactor)
            if category:
                query = query.filter(EmissionFactor.category == category)
            if item_key:
                query = query.filter(EmissionFactor.item_key == item_key)
                
            # 1. Try matching the requested region
            record = query.filter(EmissionFactor.region == region).first()
            if not record:
                # 2. Fall back to Global region
                record = query.filter(EmissionFactor.region == "Global").first()
            if not record:
                # 3. Last resort fallback to any first match
                record = query.first()
                
        except Exception as e:
            record = None

    if record:
        cached = CachedEmissionFactor(
            category=record.category,
            item_key=record.item_key,
            display_name=record.display_name,
            factor=record.factor,
            unit=record.unit,
            region=record.region,
            source=record.source
        )
        _FACTOR_CACHE[cache_key] = cached
        return cached

    # Silently fall back to standard local factor configuration
    for f in DEFAULT_EMISSION_FACTORS:
        match = True
        if category and f["category"] != category:
            match = False
        if item_key and f["item_key"] != item_key:
            match = False
            
        # Prefer matching region if possible in offline fallback
        if match:
            f_region = f.get("region", "Global")
            if f_region == region or f_region == "Global":
                cached = CachedEmissionFactor(
                    category=f["category"],
                    item_key=f["item_key"],
                    display_name=f["display_name"],
                    factor=f["factor"],
                    unit=f["unit"],
                    region=f_region,
                    source=f.get("source", "offline_fallback")
                )
                _FACTOR_CACHE[cache_key] = cached
                return cached
                
    _FACTOR_CACHE[cache_key] = None
    return None

def get_factors_all(db: Session, category: str = None) -> list:
    """
    Queries all emission factors of a category, falling back to local static config if database fails.
    Caches results in memory to avoid repeated DB roundtrips.
    """
    if category in _ALL_FACTORS_CACHE:
        return _ALL_FACTORS_CACHE[category]
        
    records = []
    
    # Check if database is offline or degraded
    from app.database import session as db_session
    from app.database.session import check_database_health_throttled
    
    if db_session.OFFLINE_MODE or db_session.READ_ONLY_MODE or not check_database_health_throttled():
        # Bypass DB query entirely
        pass
    else:
        try:
            query = db.query(EmissionFactor)
            if category:
                query = query.filter(EmissionFactor.category == category)
            records = query.all()
        except Exception as e:
            records = []
        
    if records:
        results = []
        for record in records:
            results.append(CachedEmissionFactor(
                category=record.category,
                item_key=record.item_key,
                display_name=record.display_name,
                factor=record.factor,
                unit=record.unit,
                region=record.region,
                source=record.source
            ))
        _ALL_FACTORS_CACHE[category] = results
        return results

    # Fallback to local config
    results = []
    for f in DEFAULT_EMISSION_FACTORS:
        if not category or f["category"] == category:
            results.append(CachedEmissionFactor(
                category=f["category"],
                item_key=f["item_key"],
                display_name=f["display_name"],
                factor=f["factor"],
                unit=f["unit"],
                region=f.get("region", "Global"),
                source=f.get("source", "offline_fallback")
            ))
    _ALL_FACTORS_CACHE[category] = results
    return results

# Ingredient-based recipes for composite dishes (in kg of ingredient per portion/plate)
RECIPES = {
    "curd rice": {
        "rice": 0.200,    # 200g rice
        "curd": 0.150,    # 150g curd
    },
    "chicken biryani": {
        "rice": 0.250,    # 250g rice
        "chicken": 0.150, # 150g chicken
        "vegetables": 0.050  # 50g spices/veggies
    },
    "dosa": {
        "rice": 0.120,    # 120g rice-based batter
    },
    "idli": {
        "rice": 0.040,    # 40g rice-based batter
    },
    "vegetable curry": {
        "vegetables": 0.150,
        "milk": 0.050
    },
    "paneer butter masala": {
        "paneer": 0.150,
        "milk": 0.050,
    }
}

def calculate_food_emission(db: Session, item: str, quantity: float, unit: str, region: str = "Global", food_co2_kg: float | None = None) -> Tuple[float, Dict[str, Any]]:
    """
    Calculates carbon emissions for food.

    Fast path: if `food_co2_kg` is provided (populated by the NLP food knowledge base),
    the fixed per-serving value is used directly — no DB lookup needed.

    Fallback: composite recipe ingredients + DB emission factors.
    Returns: (calculated_emissions_kg, metadata)
    """
    # ── Fast path: pre-calculated value from food_emission_factors.py ────────
    if food_co2_kg is not None:
        total = food_co2_kg * max(quantity, 1.0)
        return total, {
            "calculation_type": "food_knowledge_base",
            "dish": item,
            "co2_per_serving_kg": food_co2_kg,
            "servings": quantity,
            "total_emissions_kg": round(total, 4),
        }


    item_clean = item.lower().strip()
    unit_clean = unit.lower().strip()

    # Determine weight in kg
    weight_kg = 0.0
    if unit_clean in ["kg", "kgs", "kilogram", "kilograms"]:
        weight_kg = quantity
    elif unit_clean in ["g", "gs", "gram", "grams"]:
        weight_kg = quantity / 1000.0
    elif unit_clean in ["plate", "plates", "bowl", "bowls", "cup", "cups", "glass", "glasses", "serving", "servings"]:
        lookup_key = f"{unit_clean[:-1] if unit_clean.endswith('s') else unit_clean} {item_clean}"
        if lookup_key in FOOD_UNIT_TO_KG:
            weight_kg = FOOD_UNIT_TO_KG[lookup_key] * quantity
        elif item_clean in FOOD_UNIT_TO_KG:
            weight_kg = FOOD_UNIT_TO_KG[item_clean] * quantity
        elif unit_clean[:-1] if unit_clean.endswith('s') else unit_clean in FOOD_UNIT_TO_KG:
            weight_kg = FOOD_UNIT_TO_KG[unit_clean[:-1] if unit_clean.endswith('s') else unit_clean] * quantity
        else:
            weight_kg = 0.250 * quantity
    else:
        if item_clean in FOOD_UNIT_TO_KG:
            weight_kg = FOOD_UNIT_TO_KG[item_clean] * quantity
        else:
            weight_kg = 0.200 * quantity

    # ── PRIMARY: Master Emission Formula Standard (Section C) ──────────────
    # FOOD_FACTORS holds approved per-serving dish factors.
    # These always take priority over the ingredient-decomposition RECIPES path.
    food_key = None
    if item_clean in FOOD_FACTORS:
        food_key = item_clean
    else:
        for f in FOOD_FACTORS:
            if f in item_clean or item_clean in f:
                food_key = f
                break

    if food_key:
        factor_info = FOOD_FACTORS[food_key]
        factor_val  = factor_info["factor"]
        source_val  = factor_info["source"]

        # quantity is servings; formula: servings × factor
        servings = max(quantity, 1.0) if unit_clean in [
            "plate", "plates", "bowl", "bowls", "cup", "cups",
            "glass", "glasses", "serving", "servings", "piece", "pieces"
        ] else quantity

        formula_res = calculate_food_co2(servings, factor_val, source_val)

        metadata = {
            "co2":     formula_res["co2"],
            "factor":  formula_res["factor"],
            "source":  formula_res["source"],
            "method":  "formula",
            # legacy compatibility keys
            "calculation_type": "per_serving",
            "mapped_item":      food_key,
            "servings":         servings,
            "emission_factor":  factor_val,
        }
        return formula_res["co2"], metadata


    # 1. Resolve composite recipe
    if item_clean in RECIPES:
        recipe = RECIPES[item_clean]
        total_emission = 0.0
        ingredients_breakdown = {}
        
        # Base factor database lookup
        for ingredient, weight_per_unit in recipe.items():
            factor_record = get_factor_first(db, item_key=ingredient, region=region)
            factor_val = factor_record.factor if factor_record else 1.0
            
            # total weight = quantity of portion * portion ingredient weight
            total_weight = quantity * weight_per_unit
            ingredient_emission = total_weight * factor_val
            total_emission += ingredient_emission
            
            ingredients_breakdown[ingredient] = {
                "weight_kg": round(total_weight, 3),
                "factor": factor_val,
                "emissions_kg": round(ingredient_emission, 4)
            }
            
        metadata = {
            "calculation_type": "recipe_based",
            "recipe_name": item_clean,
            "ingredients": ingredients_breakdown,
            "total_weight_kg": round(sum(quantity * w for w in recipe.values()), 3)
        }
        return total_emission, metadata
        
    # 2. Non-recipe fallback (direct item factor or weight conversion)
    factor_record = get_factor_first(db, item_key=item_clean, region=region)
    
    # If no direct match, check sub-strings
    if not factor_record:
        all_factors = get_factors_all(db, category="food")
        for f in all_factors:
            if f.item_key in item_clean or item_clean in f.item_key:
                factor_record = f
                break
                
    # Fallback to general vegetable factor if unknown
    if not factor_record:
        factor_record = get_factor_first(db, item_key="vegetables", region=region)
        
    factor_val = factor_record.factor if factor_record else 0.5
    item_mapped = factor_record.item_key if factor_record else "vegetables"
            
    emissions = weight_kg * factor_val
    metadata = {
        "calculation_type": "weight_based",
        "mapped_item": item_mapped,
        "estimated_weight_kg": round(weight_kg, 3),
        "emission_factor": factor_val,
    }
    return emissions, metadata

def calculate_transport_emission(db: Session, vehicle: str, distance: float, unit: str, region: str = "Global") -> Tuple[float, Dict[str, Any]]:
    """
    Calculates carbon emissions for transport.
    Formula: distance (km) * factor (kgCO2e/km)
    """
    vehicle_clean = vehicle.lower().strip()
    unit_clean = unit.lower().strip()
    
    # Convert unit to km
    distance_km = distance
    if unit_clean in ["mile", "miles", "mi"]:
        distance_km = distance * 1.60934

    # Resolve vehicle key using existing rules:
    vehicle_key = vehicle_clean
    if vehicle_clean in TRANSPORT_FACTORS:
        vehicle_key = vehicle_clean
    else:
        # Apply mapping rules
        if "car" in vehicle_clean:
            if "diesel" in vehicle_clean:
                vehicle_key = "diesel_car"
            elif "ev" in vehicle_clean or "electric" in vehicle_clean:
                vehicle_key = "electric_car"
            elif "hybrid" in vehicle_clean:
                vehicle_key = "hybrid_car"
            elif "cng" in vehicle_clean:
                vehicle_key = "cng_car"
            else:
                vehicle_key = "petrol_car"
        elif "train" in vehicle_clean or "rail" in vehicle_clean:
            if "electric" in vehicle_clean:
                vehicle_key = "electric_train"
            else:
                vehicle_key = "train"
        elif "metro" in vehicle_clean or "subway" in vehicle_clean or "tube" in vehicle_clean:
            vehicle_key = "metro"
        elif "bus" in vehicle_clean:
            if "electric" in vehicle_clean:
                vehicle_key = "electric_bus"
            else:
                vehicle_key = "bus"
        elif "flight" in vehicle_clean or "plane" in vehicle_clean or "flying" in vehicle_clean:
            vehicle_key = "flight"
        elif "bike" in vehicle_clean or "motorcycle" in vehicle_clean or "scooter" in vehicle_clean:
            if "electric" in vehicle_clean:
                if "scooter" in vehicle_clean:
                    vehicle_key = "electric_scooter"
                else:
                    vehicle_key = "electric_bike"
            else:
                vehicle_key = "bike"
        elif "rickshaw" in vehicle_clean or "auto" in vehicle_clean:
            vehicle_key = "auto_rickshaw"
        elif "walk" in vehicle_clean or "cycle" in vehicle_clean or "bicycle" in vehicle_clean:
            vehicle_key = "walking"

    # Try matching using transport_formula and TRANSPORT_FACTORS
    lookup_key = vehicle_key.replace("_", " ")
    if lookup_key in TRANSPORT_FACTORS:
        factor_info = TRANSPORT_FACTORS[lookup_key]
        factor_val = factor_info["factor"]
        source_val = factor_info["source"]
        
        formula_res = calculate_transport_co2(distance_km, factor_val, source_val)
        
        metadata = {
            "co2": formula_res["co2"],
            "factor": formula_res["factor"],
            "source": formula_res["source"],
            "method": "formula",
            # legacy keys:
            "distance_km": round(distance_km, 2),
            "vehicle_mapped": vehicle_key,
            "emission_factor": factor_val
        }
        return formula_res["co2"], metadata

    # Find matching factor (fallback)
    factor_record = get_factor_first(db, category="transport", item_key=vehicle_clean, region=region)
    
    # Fallback to general vehicle if no exact match
    if not factor_record:
        if "car" in vehicle_clean:
            if "diesel" in vehicle_clean:
                factor_record = get_factor_first(db, category="transport", item_key="diesel_car", region=region)
                if not factor_record:
                    factor_record = get_factor_first(db, category="transport", item_key="diesel car", region=region)
            elif "ev" in vehicle_clean or "electric" in vehicle_clean:
                factor_record = get_factor_first(db, category="transport", item_key="electric_car", region=region)
                if not factor_record:
                    factor_record = get_factor_first(db, category="transport", item_key="ev", region=region)
            elif "hybrid" in vehicle_clean:
                factor_record = get_factor_first(db, category="transport", item_key="hybrid_car", region=region)
            elif "cng" in vehicle_clean:
                factor_record = get_factor_first(db, category="transport", item_key="cng_car", region=region)
            else:
                factor_record = get_factor_first(db, category="transport", item_key="petrol_car", region=region)
                if not factor_record:
                    factor_record = get_factor_first(db, category="transport", item_key="petrol car", region=region)
        elif "train" in vehicle_clean or "rail" in vehicle_clean:
            if "electric" in vehicle_clean:
                factor_record = get_factor_first(db, category="transport", item_key="electric_train", region=region)
            if not factor_record:
                factor_record = get_factor_first(db, category="transport", item_key="train", region=region)
        elif "metro" in vehicle_clean or "subway" in vehicle_clean or "tube" in vehicle_clean:
            factor_record = get_factor_first(db, category="transport", item_key="metro", region=region)
        elif "bus" in vehicle_clean:
            if "electric" in vehicle_clean:
                factor_record = get_factor_first(db, category="transport", item_key="electric_bus", region=region)
            if not factor_record:
                factor_record = get_factor_first(db, category="transport", item_key="bus", region=region)
        elif "flight" in vehicle_clean or "plane" in vehicle_clean or "flying" in vehicle_clean:
            factor_record = get_factor_first(db, category="transport", item_key="flight", region=region)
        elif "bike" in vehicle_clean or "motorcycle" in vehicle_clean or "scooter" in vehicle_clean:
            if "electric" in vehicle_clean:
                if "scooter" in vehicle_clean:
                    factor_record = get_factor_first(db, category="transport", item_key="electric_scooter", region=region)
                else:
                    factor_record = get_factor_first(db, category="transport", item_key="electric_bike", region=region)
            if not factor_record:
                factor_record = get_factor_first(db, category="transport", item_key="bike", region=region)
        elif "rickshaw" in vehicle_clean or "auto" in vehicle_clean:
            factor_record = get_factor_first(db, category="transport", item_key="auto_rickshaw", region=region)
        elif "walk" in vehicle_clean or "cycle" in vehicle_clean or "bicycle" in vehicle_clean:
            factor_record = get_factor_first(db, category="transport", item_key="walking", region=region)
            
    if not factor_record:
        factor_val = 0.0
        vehicle_mapped = "unknown_transport_mode"
        source_val = "CarbonTracker Standard"
    else:
        factor_val = factor_record.factor
        vehicle_mapped = factor_record.item_key
        source_val = factor_record.source
    
    # Print debug logging output
    print(f"Detected Entity:\n{vehicle}")
    print(f"Normalized Entity:\n{vehicle_clean}")
    print(f"Factor Key Used:\n{vehicle_mapped}")
    print(f"Factor Key:\n{vehicle_mapped}")
    print(f"Retrieved Factor:\n{factor_val:.3f}")
    print(f"Factor Retrieved:\n{factor_val:.3f}")

    import logging
    logger = logging.getLogger("carbontracker.calculations")
    logger.info(f"Detected Entity: {vehicle} | Normalized Entity: {vehicle_clean} | Factor Key: {vehicle_mapped} | Factor Retrieved: {factor_val}")

    emissions = distance_km * factor_val
    metadata = {
        "distance_km": round(distance_km, 2),
        "vehicle_mapped": vehicle_mapped,
        "emission_factor": factor_val,
        "source": factor_record.source if factor_record else "estimated"
    }
    return emissions, metadata

def calculate_appliance_emission(db: Session, appliance: str, duration_hours: float, quantity: float = 1.0, region: str = "Global") -> Tuple[float, Dict[str, Any]]:
    """
    Calculates carbon emissions for appliance usage.
    Appliance Wattage x Hours x Region Grid Electricity Factor.
    """
    appliance_clean = appliance.lower().strip().replace("_", " ")
    
    # Resolve appliance key in APPLIANCE_WATTS
    appliance_key = None
    if appliance_clean in APPLIANCE_WATTS:
        appliance_key = appliance_clean
    else:
        # Fallback mappings to match APPLIANCE_WATTS keys
        if "ac" in appliance_clean or "air conditioner" in appliance_clean or "cooling" in appliance_clean:
            appliance_key = "ac"
        elif "fan" in appliance_clean or "cooler" in appliance_clean:
            appliance_key = "fan"
        elif "fridge" in appliance_clean or "refrigerator" in appliance_clean:
            appliance_key = "refrigerator"
        elif "laptop" in appliance_clean or "computer" in appliance_clean or "pc" in appliance_clean:
            appliance_key = "laptop"
        elif "tv" in appliance_clean or "television" in appliance_clean:
            appliance_key = "tv"
        elif "washing" in appliance_clean or "dryer" in appliance_clean or "washer" in appliance_clean:
            appliance_key = "washing machine"
        elif "heater" in appliance_clean or "geyser" in appliance_clean:
            appliance_key = "water heater"
        elif "light" in appliance_clean or "bulb" in appliance_clean or "lamp" in appliance_clean:
            appliance_key = "lights"

    # Get grid factor based on region
    region_clean = region.lower().strip()
    if region_clean in GRID_FACTORS:
        grid_key = region_clean
    else:
        grid_key = "global"
        
    grid_info = GRID_FACTORS[grid_key]
    grid_factor = grid_info["factor"]
    grid_source = grid_info["source"]
    
    if appliance_key:
        watts = APPLIANCE_WATTS[appliance_key]["factor"]
        appliance_source = APPLIANCE_WATTS[appliance_key]["source"]
        
        # Calculate emissions using appliance_formula
        total_hours = duration_hours * quantity
        formula_res = calculate_appliance_co2(watts, total_hours, grid_factor, grid_source)
        
        total_kwh = (watts * duration_hours * quantity) / 1000.0
        
        metadata = {
            "co2": formula_res["co2"],
            "factor": formula_res["factor"],
            "source": formula_res["source"],
            "method": "formula",
            # legacy keys:
            "appliance_mapped": appliance_key,
            "appliance_watts": watts,
            "duration_hours": duration_hours,
            "quantity": quantity,
            "total_kwh": round(total_kwh, 4),
            "grid_emission_factor": grid_factor,
            "region_applied": region,
            "grid_source": grid_source
        }
        return formula_res["co2"], metadata

    # Get the appliance wattage from database/fallback
    factor_record = get_factor_first(db, category="appliances", item_key=appliance_clean, region=region)
    
    # Fallback mappings
    if not factor_record:
        if "ac" in appliance_clean or "air conditioner" in appliance_clean or "cooling" in appliance_clean:
            factor_record = get_factor_first(db, category="appliances", item_key="ac", region=region)
        elif "fan" in appliance_clean or "cooler" in appliance_clean:
            factor_record = get_factor_first(db, category="appliances", item_key="fan", region=region)
        elif "fridge" in appliance_clean or "refrigerator" in appliance_clean:
            factor_record = get_factor_first(db, category="appliances", item_key="refrigerator", region=region)
        elif "laptop" in appliance_clean or "computer" in appliance_clean or "pc" in appliance_clean:
            factor_record = get_factor_first(db, category="appliances", item_key="laptop", region=region)
        elif "tv" in appliance_clean or "television" in appliance_clean:
            factor_record = get_factor_first(db, category="appliances", item_key="tv", region=region)
        elif "washing" in appliance_clean or "dryer" in appliance_clean or "washer" in appliance_clean:
            factor_record = get_factor_first(db, category="appliances", item_key="washing machine", region=region)
        elif "heater" in appliance_clean or "geyser" in appliance_clean:
            factor_record = get_factor_first(db, category="appliances", item_key="water heater", region=region)
        elif "light" in appliance_clean or "bulb" in appliance_clean or "lamp" in appliance_clean:
            factor_record = get_factor_first(db, category="appliances", item_key="lights", region=region)
            
    if not factor_record:
        watts = 150.0
        appliance_mapped = "unknown_appliance"
    else:
        watts = factor_record.factor
        appliance_mapped = factor_record.item_key
        
    # Calculate kWh
    kwh = (watts * duration_hours * quantity) / 1000.0
    
    # MANDATORY grid factor = 0.82 kg CO2e/kWh (Master Emission Formula Standard)
    grid_factor = 0.82
    grid_source = "CarbonTracker Standard"
    
    emissions = kwh * grid_factor
    
    metadata = {
        "appliance_mapped": appliance_mapped,
        "appliance_watts": watts,
        "duration_hours": duration_hours,
        "quantity": quantity,
        "total_kwh": round(kwh, 4),
        "grid_emission_factor": grid_factor,
        "region_applied": region,
        "grid_source": grid_source
    }
    
    return emissions, metadata

def calculate_generic_emission(db: Session, category: str, item: str, quantity: float, unit: str, region: str = "Global") -> Tuple[float, Dict[str, Any]]:
    """
    Calculates carbon emissions for generic categories.
    """
    category_clean = category.lower().strip()
    item_clean = item.lower().strip()
    unit_clean = unit.lower().strip()
    
    if category_clean == "exercise":
        metadata = {
            "item_mapped": item_clean,
            "quantity_input": quantity,
            "unit_input": unit,
            "quantity_calculated": quantity,
            "unit_calculated": unit,
            "emission_factor": 0.0,
            "source": "Calculated",
            "method": "Human Powered"
        }
        return 0.0, metadata

    if item_clean in ["needs clarification", "unknown"]:
        metadata = {
            "item_mapped": "Unknown",
            "quantity_input": quantity,
            "unit_input": unit,
            "quantity_calculated": quantity,
            "unit_calculated": unit,
            "emission_factor": 0.0,
            "source": "Calculated",
            "method": "Unknown"
        }
        return 0.0, metadata

    # ── Waste Category ──────────────────────────────────────────────────
    if category_clean == "waste":
        waste_key = None
        if item_clean in WASTE_FACTORS:
            waste_key = item_clean
        else:
            for w in WASTE_FACTORS:
                if w in item_clean or item_clean in w:
                    waste_key = w
                    break
        
        weight_kg = quantity
        if unit_clean in ["g", "gs", "gram", "grams"]:
            weight_kg = quantity / 1000.0
            
        if waste_key:
            factor_info = WASTE_FACTORS[waste_key]
            factor_val = factor_info["factor"]
            source_val = factor_info["source"]
            
            formula_res = calculate_waste_co2(weight_kg, factor_val, source_val)
            
            metadata = {
                "co2": formula_res["co2"],
                "factor": formula_res["factor"],
                "source": formula_res["source"],
                "method": "formula",
                # legacy keys:
                "item_mapped": waste_key,
                "quantity_input": quantity,
                "unit_input": unit,
                "quantity_calculated": round(weight_kg, 2),
                "unit_calculated": "kg",
                "emission_factor": factor_val
            }
            return formula_res["co2"], metadata

    # ── Shopping Category ───────────────────────────────────────────────
    if category_clean == "shopping":
        shopping_key = None
        if item_clean in SHOPPING_FACTORS:
            shopping_key = item_clean
        else:
            for s in SHOPPING_FACTORS:
                if s in item_clean or item_clean in s:
                    shopping_key = s
                    break
                    
        if shopping_key:
            factor_info = SHOPPING_FACTORS[shopping_key]
            factor_val = factor_info["factor"]
            source_val = factor_info["source"]
            
            formula_res = calculate_shopping_co2(quantity, factor_val, source_val)
            
            metadata = {
                "co2": formula_res["co2"],
                "factor": formula_res["factor"],
                "source": formula_res["source"],
                "method": "formula",
                # legacy keys:
                "item_mapped": shopping_key,
                "quantity_input": quantity,
                "unit_input": unit,
                "quantity_calculated": quantity,
                "unit_calculated": "items",
                "emission_factor": factor_val
            }
            return formula_res["co2"], metadata
    
    factor_record = get_factor_first(db, category=category_clean, item_key=item_clean, region=region)
    
    # Fallback to substring matching
    if not factor_record:
        all_cat_factors = get_factors_all(db, category=category_clean)
        for f in all_cat_factors:
            if f.item_key in item_clean or item_clean in f.item_key:
                factor_record = f
                break
                
    if not factor_record:
        fallbacks = {
            "shopping": 5.0,
            "waste": 0.8,
            "water": 0.0003,
            "lifestyle": 1.0
        }
        factor_val = fallbacks.get(category_clean, 1.0)
        item_mapped = "generic_" + category_clean
        unit_mapped = "units"
        source = "estimated"
    else:
        factor_val = factor_record.factor
        item_mapped = factor_record.item_key
        unit_mapped = factor_record.unit
        source = factor_record.source
        
    scale = 1.0
    if category_clean == "water" and unit_clean in ["gallon", "gallons", "gal"]:
        scale = 3.78541
        
    final_quantity = quantity * scale
    emissions = final_quantity * factor_val
    
    metadata = {
        "item_mapped": item_mapped,
        "quantity_input": quantity,
        "unit_input": unit,
        "quantity_calculated": round(final_quantity, 2),
        "unit_calculated": unit_mapped,
        "emission_factor": factor_val,
        "source": source
    }
    
    return emissions, metadata
