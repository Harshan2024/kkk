# food_factors.py
# Approved food emission factors (kg CO2e per serving)
# Source: CARBONTRACKER MASTER EMISSION FORMULA STANDARD — Section C
#
# Unit: 1 serving (unless quantity explicitly provided)
# Formula: Carbon (kg) = Quantity × Factor

FOOD_FACTORS = {
    # Salads & vegetarian staples
    "vegetable salad":   {"factor": 0.20, "source": "CarbonTracker Standard"},
    "salad":             {"factor": 0.20, "source": "CarbonTracker Standard"},

    # South Indian staples
    "idli":              {"factor": 0.12, "source": "CarbonTracker Standard"},
    "idly":              {"factor": 0.12, "source": "CarbonTracker Standard"},
    "dosa":              {"factor": 0.18, "source": "CarbonTracker Standard"},

    # Rice dishes
    "sambar rice":       {"factor": 0.45, "source": "CarbonTracker Standard"},
    "rasam rice":        {"factor": 0.35, "source": "CarbonTracker Standard"},
    "curd rice":         {"factor": 0.40, "source": "CarbonTracker Standard"},
    "egg rice":          {"factor": 0.80, "source": "CarbonTracker Standard"},
    "chicken rice":      {"factor": 1.60, "source": "CarbonTracker Standard"},
    "mutton rice":       {"factor": 3.00, "source": "CarbonTracker Standard"},

    # Noodles
    "veg noodles":       {"factor": 0.50, "source": "CarbonTracker Standard"},
    "egg noodles":       {"factor": 0.85, "source": "CarbonTracker Standard"},
    "chicken noodles":   {"factor": 1.70, "source": "CarbonTracker Standard"},

    # Biriyani
    "chicken biriyani":  {"factor": 2.50, "source": "CarbonTracker Standard"},
    "chicken biryani":   {"factor": 2.50, "source": "CarbonTracker Standard"},
    "chicken biriyani":  {"factor": 2.50, "source": "CarbonTracker Standard"},
    "mutton biriyani":   {"factor": 3.50, "source": "CarbonTracker Standard"},
    "mutton biryani":    {"factor": 3.50, "source": "CarbonTracker Standard"},

    # Beverages
    "tea":               {"factor": 0.05, "source": "CarbonTracker Standard"},
    "coffee":            {"factor": 0.08, "source": "CarbonTracker Standard"},

    # Sweets & desserts
    "chocolate":         {"factor": 0.25, "source": "CarbonTracker Standard"},
    "cake":              {"factor": 0.40, "source": "CarbonTracker Standard"},
    "ice cream":         {"factor": 0.30, "source": "CarbonTracker Standard"},
    "candy":             {"factor": 0.05, "source": "CarbonTracker Standard"},
    "sweets":            {"factor": 0.20, "source": "CarbonTracker Standard"},
}
