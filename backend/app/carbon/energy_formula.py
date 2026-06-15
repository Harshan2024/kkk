from decimal import Decimal, ROUND_HALF_UP
from app.carbon.grid_factors import GRID_FACTOR_INDIA


def watts_to_kw(watts: float) -> float:
    """Formula 1: Convert Watts to Kilowatts.
    kW = Watts / 1000
    """
    return float(Decimal(str(watts)) / Decimal("1000"))


def minutes_to_hours(minutes: float) -> float:
    """Formula 2: Convert minutes to hours.
    Hours = Minutes / 60
    """
    return float(Decimal(str(minutes)) / Decimal("60"))


def calculate_energy_kwh(power_kw: float, duration_hours: float) -> float:
    """Formula 3: Calculate energy consumption in kWh.
    Energy (kWh) = Power (kW) × Duration (Hours)
    """
    kw = Decimal(str(power_kw))
    h = Decimal(str(duration_hours))
    return float(kw * h)


def calculate_carbon(energy_kwh: float, grid_factor: float = GRID_FACTOR_INDIA) -> float:
    """Formula 4: Calculate carbon emissions in kg CO₂.
    Carbon (kg CO₂) = Energy (kWh) × Grid Factor
    Rounded to 2 decimal places using ROUND_HALF_UP.
    """
    kwh = Decimal(str(energy_kwh))
    gf = Decimal(str(grid_factor))
    result = kwh * gf
    return float(result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def format_energy_formula(energy_kwh: float, grid_factor: float = GRID_FACTOR_INDIA) -> str:
    """Formats the calculation as a string like '4.5 × 0.82'."""
    # Show kWh to 4 significant decimal places, drop trailing zeros
    kwh_dec = Decimal(str(energy_kwh))
    # Normalize: remove trailing zeros but keep up to 4 decimal places
    kwh_str = f"{float(kwh_dec):.4f}".rstrip("0").rstrip(".")
    # If it rounds to a clean number, keep at least 4 decimals for clarity
    if "." not in kwh_str:
        kwh_str = f"{float(kwh_dec):.1f}"
    gf_str = f"{grid_factor}"
    return "%s x %s" % (kwh_str, gf_str)
