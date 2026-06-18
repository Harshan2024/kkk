# shopping_factors.py
# Approved shopping emission factors (kg CO2e per item)
# Source: CARBONTRACKER MASTER EMISSION FORMULA STANDARD — Section D
#
# Formula: Carbon (kg) = Quantity × Factor

SHOPPING_FACTORS = {
    # Electronics
    "laptop":           {"factor": 300.0, "source": "CarbonTracker Standard"},
    "smartphone":       {"factor": 70.0,  "source": "CarbonTracker Standard"},
    "phone":            {"factor": 70.0,  "source": "CarbonTracker Standard"},
    "tablet":           {"factor": 100.0, "source": "CarbonTracker Standard"},
    "television":       {"factor": 350.0, "source": "CarbonTracker Standard"},
    "tv":               {"factor": 350.0, "source": "CarbonTracker Standard"},
    "electronics":      {"factor": 80.0,  "source": "CarbonTracker Standard"},

    # Appliances
    "refrigerator":     {"factor": 400.0, "source": "CarbonTracker Standard"},
    "fridge":           {"factor": 400.0, "source": "CarbonTracker Standard"},
    "washing machine":  {"factor": 250.0, "source": "CarbonTracker Standard"},

    # Transport equipment
    "bicycle":          {"factor": 120.0, "source": "CarbonTracker Standard"},

    # Clothing & footwear
    "t-shirt":          {"factor": 5.0,   "source": "CarbonTracker Standard"},
    "shirt":            {"factor": 6.0,   "source": "CarbonTracker Standard"},
    "jeans":            {"factor": 25.0,  "source": "CarbonTracker Standard"},
    "shoes":            {"factor": 15.0,  "source": "CarbonTracker Standard"},
    "clothing":         {"factor": 6.0,   "source": "CarbonTracker Standard"},
}
