# appliance_formula.py
from decimal import Decimal, ROUND_HALF_UP

def calculate_emissions(watts: float, hours: float, grid_factor: float) -> float:
    """Computes appliance carbon emissions rounded to 2 decimal places using ROUND_HALF_UP.
    Formula: (Watts * Hours / 1000) * Grid_Factor
    """
    w = Decimal(str(watts))
    h = Decimal(str(hours))
    gf = Decimal(str(grid_factor))
    kw = w / Decimal("1000")
    kwh = kw * h
    val = kwh * gf
    rounded = val.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return float(rounded)

def calculate_appliance_co2(watts: float, hours: float, grid_factor: float, source: str) -> dict:
    """Computes appliance carbon emissions and returns unified formula output schema."""
    co2 = calculate_emissions(watts, hours, grid_factor)
    return {
        "co2": co2,
        "factor": grid_factor,
        "source": source,
        "method": "formula"
    }
