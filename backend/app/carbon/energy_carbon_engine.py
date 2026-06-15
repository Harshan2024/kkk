"""
energy_carbon_engine.py
=======================
CarbonTracker AI — Phase C2 Energy Carbon Engine

Main Function:
    calculate_energy_carbon(device, power, duration, duration_unit) → dict

Pipeline:
    Power (Watts)
        ↓
    Power (kW)
        ↓
    Energy Consumption (kWh)
        ↓
    Carbon Emission (kg CO₂)

Validation Rules:
    - Power > 0 and Power <= MAX_POWER_WATTS (10000 W)
    - Duration > 0 and Duration_hours <= MAX_DURATION_HOURS (168 h = 1 week)

Power Priority:
    Rule 1: User-supplied power always wins.
    Rule 2: If no power supplied, use device_power_catalog lookup.
"""

from typing import Optional

from app.carbon.grid_factors import GRID_FACTOR_INDIA
from app.carbon.device_power_catalog import get_device_power
from app.carbon.energy_formula import (
    watts_to_kw,
    minutes_to_hours,
    calculate_energy_kwh,
    calculate_carbon,
    format_energy_formula,
)

# Safety limits
MAX_POWER_WATTS = 10_000       # 10 kW — realistic upper bound
MAX_DURATION_HOURS = 168       # 1 week


def calculate_energy_carbon(
    device: str,
    power: Optional[float] = None,
    duration: float = 0.0,
    duration_unit: str = "hours",
) -> dict:
    """
    Calculate energy carbon emissions for a device.

    Parameters
    ----------
    device        : Canonical device name (e.g., "AC", "Laptop Charger")
    power         : Power in Watts. If None, catalog value is used.
    duration      : Time value (in hours or minutes per duration_unit).
    duration_unit : "hours" or "minutes". Defaults to "hours".

    Returns
    -------
    Explainable dict with co2, formula, energy_kwh, etc.
    or {"error": "invalid_power" | "invalid_duration" | "unknown_device"}
    """

    # ── 1. Resolve Power ────────────────────────────────────────────────
    # Rule 1: User-supplied power wins
    # Rule 2: Fall back to catalog
    resolved_power = power

    if resolved_power is None:
        catalog_power = get_device_power(device)
        if catalog_power is None:
            return {
                "error": "unknown_device",
                "message": (
                    f"Device '{device}' not found in catalog. "
                    "Please provide power in Watts explicitly."
                ),
            }
        resolved_power = float(catalog_power)
    else:
        resolved_power = float(resolved_power)

    # ── 2. Validate Power ───────────────────────────────────────────────
    if resolved_power <= 0 or resolved_power > MAX_POWER_WATTS:
        return {"error": "invalid_power"}

    # ── 3. Resolve Duration → Hours ─────────────────────────────────────
    unit_lower = duration_unit.lower().strip()
    if unit_lower in ("minutes", "minute", "min", "mins"):
        duration_hours = minutes_to_hours(duration)
    else:
        duration_hours = float(duration)

    # ── 4. Validate Duration ────────────────────────────────────────────
    if duration_hours <= 0:
        return {"error": "invalid_duration"}
    if duration_hours > MAX_DURATION_HOURS:
        return {"error": "invalid_duration"}

    # ── 5. Compute Energy & Carbon ──────────────────────────────────────
    power_kw = watts_to_kw(resolved_power)
    energy_kwh = calculate_energy_kwh(power_kw, duration_hours)
    co2 = calculate_carbon(energy_kwh, GRID_FACTOR_INDIA)
    formula = format_energy_formula(energy_kwh, GRID_FACTOR_INDIA)

    # ── 6. Build Explainable Output ─────────────────────────────────────
    return {
        "device":         device,
        "power_watts":    resolved_power,
        "duration_hours": round(duration_hours, 4),
        "energy_kwh":     round(energy_kwh, 6),
        "grid_factor":    GRID_FACTOR_INDIA,
        "formula":        formula,
        "co2":            co2,
        "unit":           "kg CO₂",
    }
