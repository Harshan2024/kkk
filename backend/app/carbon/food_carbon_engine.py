"""
food_carbon_engine.py
=====================
CarbonTracker AI — Phase C3 Food Carbon Engine

Main Pipeline:
    Input Text
        ↓
    Intent Detection (food intent confirmed upstream)
        ↓
    Food Entity Recognition (spaCy tokenization + longest-phrase matching)
        ↓
    Serving Extraction (digit/textual number extraction from spaCy tokens)
        ↓
    Food Carbon Engine  (deterministic factor lookup)
        ↓
    Carbon Output

Design Rules:
    1. spaCy is used ONLY for text preprocessing and tokenization.
    2. All carbon calculations are deterministic and factor-based.
    3. Never guess or fabricate food items.
    4. Unknown food → {"error": "unknown_food_item"}.
    5. Longest phrase matching prevents partial matches (e.g. "Chicken Biriyani" > "Chicken").
    6. Default serving = 1 if no numeric quantity is found.

API
---
calculate_food_carbon_from_text(text: str) → dict
    Single food entity detected → single result dict.
    Returns {"error": "unknown_food_item"} if nothing matched.

extract_all_food_items(text: str) → list[dict]
    Multi-food detection — returns list of result dicts (one per food found).
    Used for compound inputs like "chicken biriyani and egg noodles".
"""

from __future__ import annotations

import re
from typing import Optional

from app.carbon.food_factors import lookup_food_from_text, FOOD_KEYWORD_INDEX, FOOD_FACTORS
from app.carbon.food_formula import calculate_food_carbon, format_food_formula

# ---------------------------------------------------------------------------
# Textual number → float mapping (mirrors spacy_service.py for consistency)
# ---------------------------------------------------------------------------
TEXT_NUMBERS: dict[str, float] = {
    "a": 1.0, "an": 1.0, "one": 1.0, "two": 2.0, "three": 3.0, "four": 4.0,
    "five": 5.0, "six": 6.0, "seven": 7.0, "eight": 8.0, "nine": 9.0, "ten": 10.0,
    "twice": 2.0, "thrice": 3.0, "double": 2.0,
}

# Eating/consumption verbs to skip during serving extraction
FOOD_SKIP_TOKENS = {
    "ate", "eat", "eating", "had", "have", "having", "ordered", "order",
    "consumed", "consume", "drank", "drink", "drinking", "bought", "bought",
}

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_spacy_nlp():
    """Safely returns the pre-loaded spaCy model (loaded at startup)."""
    try:
        from app.nlp.spacy_service import get_spacy_nlp
        return get_spacy_nlp()
    except Exception:
        return None


def _extract_servings_from_text(text: str) -> float:
    """
    Extracts serving count from text using spaCy tokenization.

    Priority:
        1. Numeric digits (e.g. "2 chicken biriyani" → 2)
        2. Textual numbers (e.g. "three dosa" → 3.0)
        3. Default → 1

    Skips known eating-action verbs and pure unit words.
    Returns the first valid number found.
    """
    nlp = _get_spacy_nlp()

    if nlp:
        doc = nlp(text)
        for token in doc:
            t_lower = token.text.lower()

            # Skip food/eating verbs
            if t_lower in FOOD_SKIP_TOKENS:
                continue

            # Digit / float token
            if token.like_num or token.pos_ == "NUM":
                try:
                    val = float(token.text)
                    if val > 0:
                        return int(val) if val.is_integer() else val
                except ValueError:
                    pass

            # Textual number
            if t_lower in TEXT_NUMBERS:
                return TEXT_NUMBERS[t_lower]
    else:
        # Fallback: simple regex digit search
        match = re.search(r'\b(\d+(?:\.\d+)?)\b', text)
        if match:
            val = float(match.group(1))
            if val > 0:
                return int(val) if val.is_integer() else val

        # Fallback: textual numbers
        for word in re.findall(r'\b\w+\b', text.lower()):
            if word in TEXT_NUMBERS:
                return TEXT_NUMBERS[word]

    return 1  # Default serving = 1


def _build_single_result(
    food_match: dict,
    servings: float,
) -> dict:
    """
    Constructs a single food carbon result dict from a matched food and servings.

    Returns
    -------
    {
        "food":       str,    # Display name, e.g. "Chicken Biriyani"
        "servings":   float,  # e.g. 2
        "factor":     float,  # e.g. 2.50
        "formula":    str,    # e.g. "2 × 2.50"
        "co2":        float,  # e.g. 5.00
        "unit":       str,    # "kg CO₂"
        "source":     str,    # "CarbonTracker Standard"
    }
    """
    factor = food_match["factor"]
    co2 = calculate_food_carbon(servings, factor)
    formula = format_food_formula(servings, factor)

    return {
        "food":     food_match["display_name"],
        "servings": servings,
        "factor":   factor,
        "formula":  formula,
        "co2":      co2,
        "unit":     "kg CO₂",
        "source":   "CarbonTracker Standard",
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def calculate_food_carbon_from_text(text: str) -> dict:
    """
    Main food carbon engine entry point.

    Detects the FIRST (longest-matched) food entity in text,
    extracts serving count, and returns the carbon calculation.

    Parameters
    ----------
    text : Raw user input, e.g. "I ate 2 chicken biriyani"

    Returns
    -------
    Single result dict on success, or {"error": "unknown_food_item"} if no
    food entity is recognised.
    """
    if not text or not text.strip():
        return {"error": "unknown_food_item"}

    food_match = lookup_food_from_text(text)
    if food_match is None:
        return {"error": "unknown_food_item"}

    servings = _extract_servings_from_text(text)
    return _build_single_result(food_match, servings)


def extract_all_food_items(text: str) -> list[dict]:
    """
    Multi-food entity detection.

    Scans the full text and collects ALL non-overlapping food matches
    (longest-first), each with its own serving count derived from the
    nearest preceding numeric token. This supports compound inputs like:

        "I ate chicken biriyani and egg noodles"

    Returns
    -------
    list[dict]: One result dict per food found.
    If no food is found: [{"error": "unknown_food_item"}]
    """
    if not text or not text.strip():
        return [{"error": "unknown_food_item"}]

    text_lower = text.lower()
    matches = []
    consumed_spans: list[tuple[int, int]] = []   # (start, end) of matched regions

    for keyword, canonical_key in FOOD_KEYWORD_INDEX:
        factor = FOOD_FACTORS.get(canonical_key)
        if factor is None:
            continue

        pattern = re.compile(r'\b' + re.escape(keyword) + r'\b')
        for m in pattern.finditer(text_lower):
            start, end = m.start(), m.end()

            # Skip if this span overlaps a previously matched span
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
                "keyword_matched": keyword,
            })

    if not matches:
        return [{"error": "unknown_food_item"}]

    # Sort matches by start position to process positionally
    matches.sort(key=lambda x: x["start"])
    results: list[dict] = []
    
    for idx, match in enumerate(matches):
        prev_end = 0 if idx == 0 else matches[idx - 1]["end"]
        # Extract serving from the segment after the previous match up to current match's end
        segment = text[prev_end:match["end"]]
        servings = _extract_servings_from_text(segment)

        food_match = {
            "canonical_key":   match["canonical_key"],
            "display_name":    match["canonical_key"].title(),
            "factor":          match["factor"],
            "keyword_matched": match["keyword_matched"],
        }
        results.append(_build_single_result(food_match, servings))

    return results
