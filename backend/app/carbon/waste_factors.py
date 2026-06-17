# waste_factors.py
# Standard waste emission factors in kgCO2e per kg

WASTE_FACTORS = {
    "organic waste": {"factor": 0.5, "source": "EPA"},
    "plastic waste": {"factor": 2.0, "source": "Climatiq"},
    "paper waste": {"factor": 1.0, "source": "EPA"},
    "recycling": {"factor": 0.1, "source": "Calculated"}
}
