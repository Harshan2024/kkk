# transport_factors.py
# Approved transport emission factors (kg CO2e per km)
# Source: CARBONTRACKER MASTER EMISSION FORMULA STANDARD

TRANSPORT_FACTORS = {
    # Zero-emission human-powered
    "walking":              {"factor": 0.000, "source": "CarbonTracker Standard"},
    "running":              {"factor": 0.000, "source": "CarbonTracker Standard"},
    "jogging":              {"factor": 0.000, "source": "CarbonTracker Standard"},
    "cycling":              {"factor": 0.000, "source": "CarbonTracker Standard"},
    "bicycle":              {"factor": 0.000, "source": "CarbonTracker Standard"},

    # Cars
    "petrol car":           {"factor": 0.192, "source": "CarbonTracker Standard"},
    "petrol_car":           {"factor": 0.192, "source": "CarbonTracker Standard"},
    "diesel car":           {"factor": 0.171, "source": "CarbonTracker Standard"},
    "diesel_car":           {"factor": 0.171, "source": "CarbonTracker Standard"},
    "cng car":              {"factor": 0.110, "source": "CarbonTracker Standard"},
    "cng_car":              {"factor": 0.110, "source": "CarbonTracker Standard"},
    "hybrid car":           {"factor": 0.095, "source": "CarbonTracker Standard"},
    "hybrid_car":           {"factor": 0.095, "source": "CarbonTracker Standard"},
    "electric car":         {"factor": 0.053, "source": "CarbonTracker Standard"},
    "ev":                   {"factor": 0.053, "source": "CarbonTracker Standard"},

    # Two-wheelers
    "petrol motorcycle":    {"factor": 0.103, "source": "CarbonTracker Standard"},
    "petrol bike":          {"factor": 0.103, "source": "CarbonTracker Standard"},
    "motor bike":           {"factor": 0.103, "source": "CarbonTracker Standard"},
    "motorcycle":           {"factor": 0.103, "source": "CarbonTracker Standard"},
    "bike":                 {"factor": 0.103, "source": "CarbonTracker Standard"},
    "scooter":              {"factor": 0.075, "source": "CarbonTracker Standard"},
    "petrol scooter":       {"factor": 0.075, "source": "CarbonTracker Standard"},
    "electric scooter":     {"factor": 0.015, "source": "CarbonTracker Standard"},
    "electric_scooter":     {"factor": 0.015, "source": "CarbonTracker Standard"},
    "electric bike":        {"factor": 0.020, "source": "CarbonTracker Standard"},
    "electric_bike":        {"factor": 0.020, "source": "CarbonTracker Standard"},
    "cycle":                {"factor": 0.000, "source": "CarbonTracker Standard"},

    # Three-wheelers / taxis
    "auto rickshaw":        {"factor": 0.090, "source": "CarbonTracker Standard"},
    "auto_rickshaw":        {"factor": 0.090, "source": "CarbonTracker Standard"},
    "taxi":                 {"factor": 0.192, "source": "CarbonTracker Standard"},
    "cab":                  {"factor": 0.192, "source": "CarbonTracker Standard"},

    # Buses
    "bus":                  {"factor": 0.105, "source": "CarbonTracker Standard"},
    "electric bus":         {"factor": 0.060, "source": "CarbonTracker Standard"},
    "electric_bus":         {"factor": 0.060, "source": "CarbonTracker Standard"},

    # Rail
    "train":                {"factor": 0.041, "source": "CarbonTracker Standard"},
    "electric train":       {"factor": 0.020, "source": "CarbonTracker Standard"},
    "electric_train":       {"factor": 0.020, "source": "CarbonTracker Standard"},
    "metro":                {"factor": 0.020, "source": "CarbonTracker Standard"},

    # Aviation
    "domestic flight":      {"factor": 0.255, "source": "CarbonTracker Standard"},
    "international flight": {"factor": 0.195, "source": "CarbonTracker Standard"},
    "flight":               {"factor": 0.255, "source": "CarbonTracker Standard"},

    # Water
    "ferry":                {"factor": 0.115, "source": "CarbonTracker Standard"},
    "passenger ship":       {"factor": 0.020, "source": "CarbonTracker Standard"},
}
