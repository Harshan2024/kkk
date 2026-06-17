# food_formula.py
from decimal import Decimal, ROUND_HALF_UP

def calculate_emissions(weight_kg: float, factor: float) -> float:
    """Computes food carbon emissions rounded to 2 decimal places using ROUND_HALF_UP."""
    w = Decimal(str(weight_kg))
    f = Decimal(str(factor))
    val = w * f
    rounded = val.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return float(rounded)

def calculate_food_co2(weight_kg: float, factor: float, source: str) -> dict:
    """Computes food carbon emissions and returns unified formula output schema."""
    co2 = calculate_emissions(weight_kg, factor)
    return {
        "co2": co2,
        "factor": factor,
        "source": source,
        "method": "formula"
    }
