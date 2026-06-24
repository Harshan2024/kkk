"""
activity.py — CarbonTracker Activity Model (Phase I.1)
=======================================================
Re-exports the canonical Activity model from models.py.
Provides the `from app.models.activity import Activity` import path required by Phase I.1.

The Activity model stores the original user input text and total carbon emission.
  - activity_text  → Property alias for `input_text`   (original user input)
  - total_carbon   → Property alias for `calculated_value`
"""
from app.models.models import Activity

__all__ = ["Activity"]
