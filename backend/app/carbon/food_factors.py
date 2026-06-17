# food_factors.py
# Standard food emission factors in kgCO2e per kg

FOOD_FACTORS = {
    "beef": {"factor": 60.0, "source": "Our World In Data"},
    "chicken": {"factor": 6.9, "source": "Our World In Data"},
    "rice": {"factor": 2.7, "source": "IPCC"},
    "curd": {"factor": 2.2, "source": "Climatiq"},
    "milk": {"factor": 3.0, "source": "Our World In Data"},
    "egg": {"factor": 4.5, "source": "DEFRA"},
    "vegetables": {"factor": 0.5, "source": "IPCC"},
    "fish": {"factor": 5.4, "source": "Our World In Data"},
    "cheese": {"factor": 21.0, "source": "Our World In Data"},
    "bread": {"factor": 1.2, "source": "DEFRA"},
    "paneer": {"factor": 12.0, "source": "Climatiq"}
}
