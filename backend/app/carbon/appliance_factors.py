# appliance_factors.py
# Approved appliance wattage values (W) and mandatory grid electricity factor
# Source: CARBONTRACKER MASTER EMISSION FORMULA STANDARD
#
# MANDATORY GRID FACTOR = 0.82 kg CO2e per kWh (Section B)
# Formula: Energy (kWh) = (Watts / 1000) × Hours
#          Carbon (kg)  = Energy × 0.82

APPLIANCE_WATTS = {
    "ac":              {"factor": 1500.0, "source": "Appliance Spec"},
    "fan":             {"factor": 75.0,   "source": "Appliance Spec"},
    "refrigerator":    {"factor": 100.0,  "source": "Appliance Spec"},
    "laptop":          {"factor": 60.0,   "source": "Appliance Spec"},
    "tv":              {"factor": 100.0,  "source": "Appliance Spec"},
    "television":      {"factor": 100.0,  "source": "Appliance Spec"},
    "washing machine": {"factor": 500.0,  "source": "Appliance Spec"},
    "water heater":    {"factor": 2000.0, "source": "Appliance Spec"},
    "lights":          {"factor": 15.0,   "source": "Appliance Spec"},
}

# MANDATORY grid factor = 0.82 kg CO2e per kWh.
# Only one entry: all calculations must use this value.
GRID_FACTORS = {
    "global": {"factor": 0.82, "source": "CarbonTracker Standard"},
    "india":  {"factor": 0.82, "source": "CarbonTracker Standard"},
    "usa":    {"factor": 0.82, "source": "CarbonTracker Standard"},
    "california": {"factor": 0.82, "source": "CarbonTracker Standard"},
    "germany": {"factor": 0.82, "source": "CarbonTracker Standard"},
    "france":  {"factor": 0.82, "source": "CarbonTracker Standard"},
}

# Single canonical constant — use this everywhere
MANDATORY_GRID_FACTOR = 0.82
