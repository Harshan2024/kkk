# waste_factors.py
# Approved waste emission factors (kg CO2e per kg of waste)
# Source: CARBONTRACKER MASTER EMISSION FORMULA STANDARD — Section E
#
# Formula: Carbon (kg) = Weight (kg) × Factor

WASTE_FACTORS = {
    "plastic waste":    {"factor": 6.0,  "source": "CarbonTracker Standard"},
    "plastic":          {"factor": 6.0,  "source": "CarbonTracker Standard"},

    "e-waste":          {"factor": 12.0, "source": "CarbonTracker Standard"},
    "ewaste":           {"factor": 12.0, "source": "CarbonTracker Standard"},
    "electronic waste": {"factor": 12.0, "source": "CarbonTracker Standard"},

    "battery waste":    {"factor": 15.0, "source": "CarbonTracker Standard"},
    "battery":          {"factor": 15.0, "source": "CarbonTracker Standard"},

    "organic waste":    {"factor": 0.5,  "source": "CarbonTracker Standard"},
    "food waste":       {"factor": 0.8,  "source": "CarbonTracker Standard"},
    "paper waste":      {"factor": 1.3,  "source": "CarbonTracker Standard"},
    "paper":            {"factor": 1.3,  "source": "CarbonTracker Standard"},
    "glass waste":      {"factor": 0.9,  "source": "CarbonTracker Standard"},
    "glass":            {"factor": 0.9,  "source": "CarbonTracker Standard"},
    "metal waste":      {"factor": 2.1,  "source": "CarbonTracker Standard"},
    "metal":            {"factor": 2.1,  "source": "CarbonTracker Standard"},
    "recycling":        {"factor": 0.1,  "source": "CarbonTracker Standard"},
}
