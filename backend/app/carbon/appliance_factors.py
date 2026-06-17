# appliance_factors.py
# Standard appliance wattage values (W) and regional grid electricity factors (kgCO2e per kWh)

APPLIANCE_WATTS = {
    "ac": {"factor": 1500.0, "source": "Appliance Spec"},
    "fan": {"factor": 75.0, "source": "Appliance Spec"},
    "refrigerator": {"factor": 100.0, "source": "Appliance Spec"},
    "laptop": {"factor": 60.0, "source": "Appliance Spec"},
    "tv": {"factor": 100.0, "source": "Appliance Spec"},
    "washing machine": {"factor": 500.0, "source": "Appliance Spec"},
    "water heater": {"factor": 2000.0, "source": "Appliance Spec"},
    "lights": {"factor": 15.0, "source": "Appliance Spec"}
}

GRID_FACTORS = {
    "global": {"factor": 0.70, "source": "IEA"},
    "india": {"factor": 0.82, "source": "CEA"},
    "usa": {"factor": 0.38, "source": "EPA eGRID"},
    "california": {"factor": 0.22, "source": "CARB"},
    "germany": {"factor": 0.40, "source": "UBA"},
    "france": {"factor": 0.06, "source": "RTE"}
}
