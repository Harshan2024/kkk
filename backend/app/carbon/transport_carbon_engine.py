import time
from typing import Optional

from app.carbon.emission_factors import TRANSPORT_FACTORS
from app.carbon.distance_lookup import lookup_distance
from app.carbon.transport_formula import calculate_emissions, format_formula
from app.nlp.entity_engine import extract_entities

def calculate_transport_carbon(vehicle: str, distance: float) -> dict:
    """
    Direct transport calculation logic.
    Returns:
    {
      "vehicle": str,
      "distance": float,
      "factor": float,
      "co2": float,
      "formula": str
    } or {"error": "unknown_transport_mode"}
    """
    v_lower = vehicle.lower().strip().replace("_", " ")
    
    # Flight resolution rule: if distance < 2000 km, use domestic flight factor, else international
    if v_lower == "flight":
        if distance < 2000:
            v_lower = "domestic flight"
        else:
            v_lower = "international flight"
            
    if v_lower not in TRANSPORT_FACTORS:
        return {"error": "unknown_transport_mode"}
        
    factor = TRANSPORT_FACTORS[v_lower]
    co2 = calculate_emissions(distance, factor)
    formula = format_formula(distance, factor)
    
    # Capitalize vehicle name for return JSON
    display_vehicle = vehicle
    if v_lower == "domestic flight":
        display_vehicle = "Domestic Flight"
    elif v_lower == "international flight":
        display_vehicle = "International Flight"
    else:
        # Match display name from standard factor keys
        for k in TRANSPORT_FACTORS:
            if k == v_lower:
                display_vehicle = k.title()
                break
                
    # Determine Vehicle Type and Fuel Type using our context-aware logic
    from app.nlp.transport_entities import resolve_two_wheeler_context
    two_wheeler = resolve_two_wheeler_context(display_vehicle)
    if two_wheeler:
        vehicle_type = two_wheeler["vehicle_type"]
        fuel_type = two_wheeler["fuel_type"]
        display_vehicle = two_wheeler["vehicle"]
    else:
        v_clean = display_vehicle.lower()
        if "car" in v_clean:
            vehicle_type = "Car"
            if "electric" in v_clean or "ev" in v_clean:
                fuel_type = "Electric"
            elif "diesel" in v_clean:
                fuel_type = "Diesel"
            elif "hybrid" in v_clean:
                fuel_type = "Hybrid"
            elif "cng" in v_clean:
                fuel_type = "CNG"
            else:
                fuel_type = "Petrol"
        elif "train" in v_clean or "rail" in v_clean or "metro" in v_clean or "subway" in v_clean:
            vehicle_type = "Train"
            fuel_type = "Electric" if "electric" in v_clean or "metro" in v_clean or "subway" in v_clean else "Diesel"
        elif "bus" in v_clean:
            vehicle_type = "Bus"
            fuel_type = "Electric" if "electric" in v_clean else "Diesel"
        elif "flight" in v_clean or "plane" in v_clean:
            vehicle_type = "Aviation"
            fuel_type = "Aviation Fuel"
        else:
            vehicle_type = display_vehicle.title()
            fuel_type = "Unknown"

    return {
        "vehicle": display_vehicle,
        "distance": distance,
        "factor": factor,
        "co2": co2,
        "formula": formula,
        "Vehicle Type": display_vehicle,
        "Fuel Type": fuel_type,
        "Emission Factor": factor,
        "Distance": distance,
        "Carbon Formula": formula,
        "CO₂ Result": co2
    }

def calculate_transport_from_text(text: str) -> dict:
    """
    Main pipeline combining Phase B parsing and Phase C1 carbon calculations.
    """
    # 1. Parse using Phase B
    ent_res = extract_entities(text)
    
    entity = ent_res.get("entity")
    if not entity or entity == "unknown":
        return {"error": "unknown_transport_mode"}
        
    ent_lower = entity.lower().strip()
    
    # Map matched exercise entity or vehicle to canonical key
    vehicle_key = ent_lower
    if ent_lower in ["running", "jogging", "walking", "cycling", "bicycle", "bicycle ride"]:
        if ent_lower == "bicycle ride":
            vehicle_key = "bicycle"
        else:
            vehicle_key = ent_lower

    # 2. Resolve distance
    distance = None
    
    # Priority 1: Explicit distance
    if "distance" in ent_res:
        distance = ent_res["distance"]
        
    # Priority 2: Predefined city lookup fallback
    if distance is None:
        source = ent_res.get("source")
        destination = ent_res.get("destination")
        if source and destination:
            distance = lookup_distance(source, destination)
            
    # Priority 3: Return distance_required error if still missing
    if distance is None:
        return {
            "error": "distance_required",
            "message": "Please specify the travel distance in kilometers."
        }
        
    # 3. Perform carbon calculation
    return calculate_transport_carbon(vehicle_key, distance)
