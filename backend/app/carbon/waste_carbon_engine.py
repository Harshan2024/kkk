"""
waste_carbon_engine.py
======================
CarbonTracker AI - Phase C4 Waste Carbon Engine

Main Pipeline:
    Input Text
        |
    Intent Detection (waste intent confirmed upstream)
        |
    Waste Entity Recognition (spaCy tokenization + longest-phrase matching)
        |
    Weight Extraction (digit/textual number + unit extraction via spaCy)
        |
    Unit Conversion (grams -> kg if needed)
        |
    Waste Carbon Engine (deterministic factor lookup)
        |
    Carbon Output

Design Rules:
    1. spaCy is used ONLY for tokenization and quantity extraction.
    2. All carbon calculations are deterministic and factor-based.
    3. Never guess or fabricate waste types.
    4. Unknown waste -> {"error": "unknown_waste_type"}.
    5. Longest phrase matching prevents partial matches.
    6. Weight unit conversion: grams / 1000 = kg before calculation.
    7. Default weight = None (weight_required error if not supplied).

API
---
calculate_waste_carbon_from_text(text: str) -> dict
    Single waste entity detected -> single result dict.
    Returns {"error": "unknown_waste_type"} if nothing matched.
    Returns {"error": "weight_required"} if no weight is found.

extract_all_waste_items(text: str) -> list[dict]
    Multi-waste detection - one result per waste type found.
    Used for compound inputs like "1 kg plastic waste and 2 kg paper waste".
"""

from __future__ import annotations

import re
from typing import Optional

from app.carbon.waste_factors import (
    lookup_waste_from_text,
    WASTE_KEYWORD_INDEX,
    WASTE_FACTORS,
    WASTE_DISPLAY_NAMES,
)
from app.carbon.waste_formula import (
    grams_to_kg,
    calculate_waste_carbon,
    format_waste_formula,
)

# ---------------------------------------------------------------------------
# Weight unit patterns
# ---------------------------------------------------------------------------
# Supported weight units and their canonical forms
WEIGHT_UNIT_MAP: dict[str, str] = {
    "kg":        "kg",
    "kilogram":  "kg",
    "kilograms": "kg",
    "g":         "g",
    "gram":      "g",
    "grams":     "g",
}

# Regex to extract numeric weight + unit from text
# Matches patterns like: "2 kg", "500 g", "1.5 kilograms", "250grams"
_WEIGHT_PATTERN = re.compile(
    r'\b(\d+(?:\.\d+)?)\s*'
    r'(kg|kilograms?|grams?|g)\b',
    re.IGNORECASE
)

# Textual number mapping (mirrors spacy_service.py)
TEXT_NUMBERS: dict[str, float] = {
    "a": 1.0, "an": 1.0, "one": 1.0, "two": 2.0, "three": 3.0, "four": 4.0,
    "five": 5.0, "six": 6.0, "seven": 7.0, "eight": 8.0, "nine": 9.0, "ten": 10.0,
    "half": 0.5, "quarter": 0.25,
}

# Disposal/recycling action verbs to skip during weight extraction
WASTE_ACTION_TOKENS = {
    "disposed", "dispose", "disposing",
    "recycled", "recycle", "recycling",
    "threw", "throw", "throwing", "discarded", "discard",
    "dumped", "dump", "dumping", "generated", "produce",
    "got", "have", "had", "i",
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_spacy_nlp():
    """Safely returns the pre-loaded spaCy model."""
    try:
        from app.nlp.spacy_service import get_spacy_nlp
        return get_spacy_nlp()
    except Exception:
        return None


def _extract_weight_from_text(text: str) -> Optional[dict]:
    """
    Extracts weight from text.

    Priority:
        1. Regex pattern match for digit + unit (e.g. "2 kg", "500 g")
        2. spaCy NUM token + following unit word
        3. Textual number + unit (e.g. "two kg")

    Returns
    -------
    dict: {"weight_kg": float, "original_value": float, "original_unit": str}
    or None if no weight found.
    """
    # Priority 1: Regex digit + unit match (most reliable)
    match = _WEIGHT_PATTERN.search(text)
    if match:
        val = float(match.group(1))
        unit_raw = match.group(2).lower()

        # Normalise unit
        if unit_raw in ("g", "gram", "grams"):
            weight_kg = grams_to_kg(val)
            return {"weight_kg": weight_kg, "original_value": val, "original_unit": "g"}
        else:
            return {"weight_kg": val, "original_value": val, "original_unit": "kg"}

    # Priority 2: spaCy tokenization for textual numbers + unit
    nlp = _get_spacy_nlp()
    if nlp:
        doc = nlp(text)
        tokens = list(doc)
        for i, token in enumerate(tokens):
            t_lower = token.text.lower()
            if t_lower in WASTE_ACTION_TOKENS:
                continue

            # Check textual number followed by unit
            if t_lower in TEXT_NUMBERS and i + 1 < len(tokens):
                next_tok = tokens[i + 1].text.lower()
                if next_tok in WEIGHT_UNIT_MAP:
                    val = TEXT_NUMBERS[t_lower]
                    unit_canonical = WEIGHT_UNIT_MAP[next_tok]
                    if unit_canonical == "g":
                        weight_kg = grams_to_kg(val)
                    else:
                        weight_kg = val
                    return {
                        "weight_kg": weight_kg,
                        "original_value": val,
                        "original_unit": unit_canonical,
                    }

    return None


def _build_single_result(waste_match: dict, weight_kg: float) -> dict:
    """
    Constructs a single waste carbon result dict.

    Returns
    -------
    {
        "waste_type": str,   # e.g. "Plastic Waste"
        "weight":     float, # e.g. 2.0
        "factor":     float, # e.g. 6.0
        "formula":    str,   # e.g. "2 x 6.0"
        "carbon":     float, # e.g. 12.0
        "unit":       str,   # "kg CO2"
    }
    """
    factor = waste_match["factor"]
    carbon = calculate_waste_carbon(weight_kg, factor)
    formula = format_waste_formula(weight_kg, factor)

    return {
        "waste_type": waste_match["display_name"],
        "weight":     weight_kg,
        "factor":     factor,
        "formula":    formula,
        "carbon":     carbon,
        "unit":       "kg CO2",
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def calculate_waste_carbon_from_text(text: str) -> dict:
    """
    Main waste carbon engine entry point.

    Detects the FIRST (longest-matched) waste entity in text,
    extracts weight (with unit conversion), and returns the carbon calculation.

    Parameters
    ----------
    text : Raw user input, e.g. "I disposed 2 kg plastic waste"

    Returns
    -------
    Single result dict on success.
    {"error": "unknown_waste_type"} if no waste entity recognised.
    {"error": "weight_required"} if no weight provided.
    """
    if not text or not text.strip():
        return {"error": "unknown_waste_type"}

    # Step 1: Entity recognition
    waste_match = lookup_waste_from_text(text)
    if waste_match is None:
        return {"error": "unknown_waste_type"}

    # Step 2: Weight extraction
    weight_info = _extract_weight_from_text(text)
    if weight_info is None:
        return {
            "error": "weight_required",
            "message": "Please specify the waste weight (e.g. 2 kg, 500 g).",
        }

    return _build_single_result(waste_match, weight_info["weight_kg"])


def extract_all_waste_items(text: str) -> list[dict]:
    """
    Multi-waste entity detection.

    Scans the full text and collects ALL non-overlapping waste matches
    (longest-first), each with its own weight extracted from the nearest
    preceding numeric token. Supports compound inputs like:

        "I disposed 1 kg plastic waste and 2 kg paper waste"

    Returns
    -------
    list[dict]: One result dict per waste type found.
    If no waste found: [{"error": "unknown_waste_type"}]
    """
    if not text or not text.strip():
        return [{"error": "unknown_waste_type"}]

    text_lower = text.lower()
    matches = []
    consumed_spans: list[tuple[int, int]] = []

    for keyword, canonical_key in WASTE_KEYWORD_INDEX:
        factor = WASTE_FACTORS.get(canonical_key)
        if factor is None:
            continue

        pattern = re.compile(r'\b' + re.escape(keyword) + r'\b')
        for m in pattern.finditer(text_lower):
            start, end = m.start(), m.end()

            # Skip overlapping spans
            overlaps = any(
                not (end <= cs or start >= ce)
                for cs, ce in consumed_spans
            )
            if overlaps:
                continue

            consumed_spans.append((start, end))
            matches.append({
                "start": start,
                "end": end,
                "canonical_key": canonical_key,
                "factor": factor,
                "keyword_matched": keyword
            })

    if not matches:
        return [{"error": "unknown_waste_type"}]

    # Sort matches by start position to process positionally
    matches.sort(key=lambda x: x["start"])
    results: list[dict] = []

    for idx, match in enumerate(matches):
        prev_end = 0 if idx == 0 else matches[idx - 1]["end"]
        # Extract weight from the segment after the previous match up to current match's end
        segment = text[prev_end:match["end"]]
        weight_info = _extract_weight_from_text(segment)
        if weight_info is None:
            results.append({
                "error": "weight_required",
                "waste_type": WASTE_DISPLAY_NAMES.get(match["canonical_key"], match["canonical_key"].title()),
                "message": "No weight found for this waste entry.",
            })
            continue

        waste_match = {
            "canonical_key":   match["canonical_key"],
            "display_name":    WASTE_DISPLAY_NAMES.get(match["canonical_key"], match["canonical_key"].title()),
            "factor":          match["factor"],
            "keyword_matched": match["keyword_matched"],
        }
        results.append(_build_single_result(waste_match, weight_info["weight_kg"]))

    return results
