# food_formula.py
# ==============================================================
# CarbonTracker AI — Phase C3 Food Carbon Engine
# Food Carbon Formula Module
#
# Approved Formula:
#   Carbon (kg CO₂) = Servings × Food Factor
#
# Example:
#   2 × Chicken Biriyani  →  2 × 2.50  =  5.00 kg CO₂
# ==============================================================

from decimal import Decimal, ROUND_HALF_UP


def calculate_food_carbon(servings: float, factor: float) -> float:
    """
    Calculate food carbon emissions.

    Formula: Carbon (kg CO₂) = Servings × Food Factor

    Uses Decimal arithmetic with ROUND_HALF_UP to ensure consistent
    rounding behaviour across all inputs.

    Parameters
    ----------
    servings : Number of servings (default 1 if not specified by user)
    factor   : Emission factor from FOOD_FACTORS table (kg CO₂ per serving)

    Returns
    -------
    float: rounded to 2 decimal places
    """
    s = Decimal(str(servings))
    f = Decimal(str(factor))
    result = s * f
    return float(result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def format_food_formula(servings: float, factor: float) -> str:
    """
    Returns a human-readable formula string.

    Examples
    --------
    1 × 2.50
    2 × 2.50
    3 × 0.18
    """
    s_str = str(int(servings)) if float(servings).is_integer() else str(round(servings, 2))
    f_str = "{:.2f}".format(factor)
    return f"{s_str} x {f_str}"


def calculate_food_co2(servings: float, factor: float, source: str) -> dict:
    """
    Wrapper for calculate_food_carbon used by app/calculations/engines.py.
    """
    co2 = calculate_food_carbon(servings, factor)
    formula = format_food_formula(servings, factor)
    return {
        "co2": co2,
        "factor": factor,
        "source": source,
        "formula": formula
    }

