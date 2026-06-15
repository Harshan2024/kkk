# Module 2 — Device Power Catalog
# Unit: Watts
# Standard appliance power ratings for India

DEVICE_POWER = {
    # Cooling
    "ac":                 1500,
    "air_conditioner":    1500,
    "air conditioner":    1500,

    # Fans
    "fan":                75,
    "ceiling_fan":        75,
    "ceiling fan":        75,
    "table_fan":          60,
    "table fan":          60,

    # Lighting
    "led_light":          10,
    "led light":          10,
    "led":                10,
    "tube_light":         40,
    "tube light":         40,
    "bulb":               60,
    "light":              15,

    # Entertainment
    "television":         100,
    "tv":                 100,

    # Kitchen
    "refrigerator":       150,
    "fridge":             150,
    "washing_machine":    500,
    "washing machine":    500,
    "water_heater":       2000,
    "water heater":       2000,
    "geyser":             2000,
    "mixer_grinder":      500,
    "mixer grinder":      500,
    "mixer":              500,

    # Computing
    "laptop":             65,
    "laptop_charger":     65,
    "laptop charger":     65,
    "mobile_charger":     20,
    "mobile charger":     20,
    "charger":            20,
    "desktop":            250,
    "computer":           250,

    # Appliances
    "iron_box":           1000,
    "iron box":           1000,
    "iron":               1000,
}


def get_device_power(device: str) -> int:
    """
    Looks up the standard power rating for a device.
    Returns power in Watts, or None if not found.
    Performs case-insensitive matching.
    """
    key = device.lower().strip().replace("-", "_")
    # Direct lookup
    if key in DEVICE_POWER:
        return DEVICE_POWER[key]
    # Try with spaces instead of underscores
    key_space = key.replace("_", " ")
    if key_space in DEVICE_POWER:
        return DEVICE_POWER[key_space]
    # Partial/substring match (longest first)
    sorted_keys = sorted(DEVICE_POWER.keys(), key=len, reverse=True)
    for catalog_key in sorted_keys:
        if catalog_key in key or key in catalog_key:
            return DEVICE_POWER[catalog_key]
    return None
