# shopping_formula.py
from decimal import Decimal, ROUND_HALF_UP

def calculate_emissions(quantity: float, factor: float) -> float:
    """Computes shopping carbon emissions rounded to 2 decimal places using ROUND_HALF_UP."""
    q = Decimal(str(quantity))
    f = Decimal(str(factor))
    val = q * f
    rounded = val.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return float(rounded)

def calculate_shopping_co2(quantity: float, factor: float, source: str) -> dict:
    """Computes shopping carbon emissions and returns unified formula output schema."""
    co2 = calculate_emissions(quantity, factor)
    return {
        "co2": co2,
        "factor": factor,
        "source": source,
        "method": "formula"
    }
