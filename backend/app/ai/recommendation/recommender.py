from typing import List, Dict, Any

# Expanded candidate pool with rich metadata for AI explanation layer and ranking
CANDIDATE_POOL = [
    {
        "content": "Swap beef for chicken or paneer/lentils to significantly lower your diet footprint.",
        "category": "food",
        "impact_value": 53.1, # Monthly saving estimate in kgCO2e
        "feasibility": "HIGH",
        "difficulty": "EASY",
        "confidence_score": 0.95,
        "sustainability_gain": 9.2,
        "behavioral_compatibility": 8.8,
        "why_explanation": "Food is a recurring source of personal carbon. Swapping high-impact red meat for poultry or plant-based proteins yields immediate, repeatable footprint reductions.",
        "how_calculation": "Calculated by subtracting chicken emissions factor (6.9 kg CO2e/kg) from beef emissions factor (60.0 kg CO2e/kg) over a standard consumption profile."
    },
    {
        "content": "Take the metro/subway instead of a petrol car for commutes to save over 80% emissions per kilometer.",
        "category": "transport",
        "impact_value": 25.4,
        "feasibility": "HIGH",
        "difficulty": "MEDIUM",
        "confidence_score": 0.90,
        "sustainability_gain": 8.0,
        "behavioral_compatibility": 7.5,
        "why_explanation": "Public electric transit is highly optimized. Replacing single-occupancy petrol vehicle travel with metro rides dramatically cuts urban commuting emissions.",
        "how_calculation": "Based on 0.192 kg CO2e/km (petrol car) vs 0.029 kg CO2e/km (metro) multiplied by average weekly commute distances."
    },
    {
        "content": "Opt for electric trains or high-occupancy sleeper buses on medium routes to bypass air travel intensity.",
        "category": "transport",
        "impact_value": 150.0,
        "feasibility": "MEDIUM",
        "difficulty": "HARD",
        "confidence_score": 0.88,
        "sustainability_gain": 9.5,
        "behavioral_compatibility": 5.0,
        "why_explanation": "Flight takeoffs and high altitudes incur severe carbon costs. Choosing rail bypasses heavy aviation fuel combustion.",
        "how_calculation": "Assumes replacing a 1000 km domestic short-haul flight (0.255 kg CO2e/km) with electric rail transport (0.041 kg CO2e/km)."
    },
    {
        "content": "Incorporate 2 plant-based days weekly, replacing meat with curd rice, vegetables, and beans.",
        "category": "food",
        "impact_value": 12.0,
        "feasibility": "HIGH",
        "difficulty": "EASY",
        "confidence_score": 0.92,
        "sustainability_gain": 7.5,
        "behavioral_compatibility": 9.0,
        "why_explanation": "A vegetarian diet has less agricultural land and methane overhead. Two dedicated days per week build a consistent sustainability routine.",
        "how_calculation": "Aggregates the carbon savings of substituting 4 meat meals per week with vegetarian meals rated at 0.5 kg CO2e each."
    },
    {
        "content": "Shift some AC cooling hours to a standard ceiling fan, saving about 1.0 kg CO2e per hour.",
        "category": "appliances",
        "impact_value": 30.0,
        "feasibility": "HIGH",
        "difficulty": "EASY",
        "confidence_score": 0.95,
        "sustainability_gain": 8.8,
        "behavioral_compatibility": 8.5,
        "why_explanation": "Compressor-based cooling draws substantial grid power. Toggling to a fan for even part of the day directly cuts appliance load.",
        "how_calculation": "Uses AC wattage (1500W) minus ceiling fan wattage (75W) multiplied by regional grid factor emissions per kWh."
    },
    {
        "content": "Switch to energy-efficient LED bulbs to reduce standby appliance and lighting consumption.",
        "category": "appliances",
        "impact_value": 5.0,
        "feasibility": "HIGH",
        "difficulty": "EASY",
        "confidence_score": 0.90,
        "sustainability_gain": 6.0,
        "behavioral_compatibility": 9.5,
        "why_explanation": "LEDs convert over 80% of energy to light rather than heat. This simple hardware swap operates 24/7 with zero lifestyle friction.",
        "how_calculation": "Calculates 85% energy saving from replacing 5 incandescent bulbs (60W) with LED equivalents (9W) run 4 hours daily."
    },
    {
        "content": "Practice waste sorting to send combustibles/compost to appropriate organic recycling paths.",
        "category": "waste",
        "impact_value": 4.5,
        "feasibility": "HIGH",
        "difficulty": "EASY",
        "confidence_score": 0.85,
        "sustainability_gain": 5.2,
        "behavioral_compatibility": 8.0,
        "why_explanation": "Landfills release heavy methane during decomposition. Proper sorting directs organic waste to composting or bio-digesters.",
        "how_calculation": "Based on organic waste diversion factor of 0.5 kg CO2e/kg diverted from municipal solid waste streams."
    },
    {
        "content": "Reduce shower duration by 3 minutes to save water heating electricity and tap consumption.",
        "category": "water",
        "impact_value": 8.5,
        "feasibility": "HIGH",
        "difficulty": "EASY",
        "confidence_score": 0.90,
        "sustainability_gain": 6.8,
        "behavioral_compatibility": 8.5,
        "why_explanation": "Hot showers consume water and heating energy. A slight time trim reduces municipal water pumping and electricity load.",
        "how_calculation": "Calculates savings of 27L water (9L/min) and the thermal energy required to heat it (using standard geyser wattage)."
    }
]

def get_recommendation_candidates() -> List[Dict[str, Any]]:
    """
    Returns the general candidate recommendations list.
    """
    return CANDIDATE_POOL
