# waste_formula.py
# ==============================================================
# CarbonTracker AI - Phase C4 Waste Carbon Engine
# Waste Carbon Formula Module
#
# Approved Formula:
#   Carbon (kg CO2) = Weight (kg) x Factor
#
# Unit Conversion:
#   grams -> kg: divide by 1000
#
# Examples:
#   2 kg Plastic Waste  -> 2 x 6.0  = 12.00 kg CO2
#   1 kg E-Waste        -> 1 x 12.0 = 12.00 kg CO2
#   500g Organic Waste  -> 0.5 x 0.5 = 0.25 kg CO2
# ==============================================================

from decimal import Decimal, ROUND_HALF_UP


def grams_to_kg(grams: float) -> float:
    """
    Converts grams to kilograms.

    Parameters
    ----------
    grams : weight in grams

    Returns
    -------
    float: weight in kg (e.g. 500g -> 0.5 kg)
    """
    g = Decimal(str(grams))
    return float(g / Decimal("1000"))


def calculate_waste_carbon(weight_kg: float, factor: float) -> float:
    """
    Calculate waste carbon emissions.

    Formula: Carbon (kg CO2) = Weight (kg) x Factor

    Uses Decimal arithmetic with ROUND_HALF_UP for consistent rounding.

    Parameters
    ----------
    weight_kg : Weight of waste in kilograms
    factor    : Emission factor from WASTE_FACTORS (kg CO2 per kg waste)

    Returns
    -------
    float: carbon emissions rounded to 2 decimal places
    """
    w = Decimal(str(weight_kg))
    f = Decimal(str(factor))
    result = w * f
    return float(result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def format_waste_formula(weight_kg: float, factor: float) -> str:
    """
    Returns a human-readable formula string.

    Examples
    --------
    2 x 6.0
    0.5 x 1.3
    1 x 12.0
    """
    # Show weight as integer if it is a whole number, else show as decimal
    if float(weight_kg).is_integer():
        w_str = str(int(weight_kg))
    else:
        w_str = str(round(weight_kg, 4)).rstrip("0").rstrip(".")

    # Show factor without trailing zeros where appropriate
    f_val = float(factor)
    if f_val == int(f_val):
        f_str = "{:.1f}".format(f_val)
    else:
        f_str = str(f_val)

    return f"{w_str} x {f_str}"


def calculate_waste_co2(weight_kg: float, factor: float, source: str) -> dict:
    """
    Wrapper for calculate_waste_carbon used by app/calculations/engines.py.
    """
    co2 = calculate_waste_carbon(weight_kg, factor)
    formula = format_waste_formula(weight_kg, factor)
    return {
        "co2": co2,
        "factor": factor,
        "source": source,
        "formula": formula
    }

