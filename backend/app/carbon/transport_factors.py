# transport_factors.py
# Standard transport emission factors in kgCO2e per km

TRANSPORT_FACTORS = {
    "walking": {"factor": 0.0, "source": "Calculated"},
    "running": {"factor": 0.0, "source": "Calculated"},
    "jogging": {"factor": 0.0, "source": "Calculated"},
    "cycling": {"factor": 0.0, "source": "Calculated"},
    "bicycle": {"factor": 0.0, "source": "Calculated"},
    
    "petrol car": {"factor": 0.192, "source": "DEFRA"},
    "petrol_car": {"factor": 0.192, "source": "DEFRA"},
    "diesel car": {"factor": 0.171, "source": "DEFRA"},
    "diesel_car": {"factor": 0.171, "source": "DEFRA"},
    "cng car": {"factor": 0.110, "source": "DEFRA"},
    "cng_car": {"factor": 0.110, "source": "DEFRA"},
    "hybrid car": {"factor": 0.095, "source": "DEFRA"},
    "hybrid_car": {"factor": 0.095, "source": "DEFRA"},
    "electric car": {"factor": 0.053, "source": "EPA"},
    "ev": {"factor": 0.053, "source": "EPA"},
    "motorcycle": {"factor": 0.072, "source": "DEFRA"},
    "bike": {"factor": 0.072, "source": "DEFRA"},
    "petrol scooter": {"factor": 0.075, "source": "DEFRA"},
    "electric scooter": {"factor": 0.015, "source": "DEFRA"},
    "electric bike": {"factor": 0.020, "source": "DEFRA"},
    "auto rickshaw": {"factor": 0.090, "source": "DEFRA"},
    "taxi": {"factor": 0.192, "source": "DEFRA"},
    "cab": {"factor": 0.192, "source": "DEFRA"},
    
    "bus": {"factor": 0.105, "source": "DEFRA"},
    "electric bus": {"factor": 0.060, "source": "DEFRA"},
    "train": {"factor": 0.041, "source": "DEFRA"},
    "electric train": {"factor": 0.020, "source": "DEFRA"},
    "metro": {"factor": 0.029, "source": "UK GHG"},
    
    "domestic flight": {"factor": 0.255, "source": "IPCC"},
    "international flight": {"factor": 0.195, "source": "IPCC"},
    "flight": {"factor": 0.255, "source": "IPCC"},
    "ferry": {"factor": 0.115, "source": "DEFRA"},
    "passenger ship": {"factor": 0.020, "source": "DEFRA"}
}
