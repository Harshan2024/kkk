import os
from typing import Dict

# Dictionary of available feature toggles and their default values
DEFAULT_FLAGS = {
    "enable_voice_ai": True,
    "enable_multimodal": True,
    "enable_forecasting": True,
    "enable_semantic_search": True,
    "FORECAST_ENABLED": False,
    "enable_smart_devices": False
}

def get_feature_flags() -> Dict[str, bool]:
    """
    Returns the resolved feature flags, reading overrides from environment variables if present.
    """
    flags = {}
    for key, default in DEFAULT_FLAGS.items():
        # Check env variable override e.g. ENABLE_VOICE_AI=false
        env_val = os.getenv(key.upper())
        if env_val is not None:
            flags[key] = env_val.lower() in ("true", "1", "yes")
        else:
            flags[key] = default
    return flags

def is_feature_enabled(feature: str) -> bool:
    """
    Checks if a specific feature is enabled.
    """
    flags = get_feature_flags()
    return flags.get(feature, False)
