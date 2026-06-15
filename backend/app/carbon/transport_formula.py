from decimal import Decimal, ROUND_HALF_UP

def calculate_emissions(distance: float, factor: float) -> float:
    """Computes carbon emissions rounded to 2 decimal places using ROUND_HALF_UP."""
    d = Decimal(str(distance))
    f = Decimal(str(factor))
    val = d * f
    rounded = val.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return float(rounded)

def format_formula(distance: float, factor: float) -> str:
    """Formats the calculation as a string like '462 × 0.020'."""
    # Format distance: drop .0 if it's a whole number
    d_val = float(distance)
    d_str = str(int(d_val)) if d_val.is_integer() else f"{d_val:.2f}"
    
    # Format factor to 3 decimal places
    f_str = f"{factor:.3f}"
    return f"{d_str} \u00d7 {f_str}"
