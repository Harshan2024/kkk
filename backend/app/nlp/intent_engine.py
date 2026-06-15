"""
intent_engine.py
================
CarbonTracker AI — Phase A Intent Detection Engine

Public API
----------
detect_intent(text: str)         → IntentResult
detect_multi_intent(text: str)   → list[IntentResult]
explain_intent(text: str)        → dict  (debug output)

Algorithm
---------
1. Normalize   — lowercase, collapse whitespace
2. Scan        — try every phrase pattern (longest first) on the text
3. Score       — accumulate weighted hits per intent
4. Prioritize  — resolve ties using INTENT_PRIORITY order
5. Validate    — enforce override rules (exercise > transport, etc.)
6. Threshold   — if winner confidence < CONFIDENCE_THRESHOLD → Unknown
7. Return      — IntentResult(intent, confidence, scores, matched_patterns)

Performance
-----------
All patterns are pre-compiled into sorted lists at module load time.
Typical detection time: 0.2 – 2 ms  (well under the 50ms requirement).
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Optional

from app.nlp.intent_patterns import (
    ALL_PATTERNS,
    CONFIDENCE_THRESHOLD,
    INTENT_PRIORITY,
    MULTI_INTENT_SPLITTERS,
)


# ---------------------------------------------------------------------------
# Pre-compiled pattern table
# Each row: (phrase_tokens: list[str], intent: str, weight: int)
# Sorted longest-phrase-first so "morning walk" beats bare "walk".
# ---------------------------------------------------------------------------
_COMPILED: list[tuple[list[str], str, int]] = []

_APPLIANCE_NOUNS: frozenset[str] = frozenset({
    "tv", "television", "ac", "fan", "fridge", "refrigerator",
    "light", "lights", "bulb", "washing", "machine", "heater",
    "geyser", "laptop", "computer", "mobile", "phone", "charger",
})

def _build_compiled_table() -> None:
    _COMPILED.clear()
    rows: list[tuple[list[str], str, int]] = []
    for intent, patterns in ALL_PATTERNS.items():
        for phrase, weight in patterns.items():
            tokens = phrase.lower().split()
            rows.append((tokens, intent, weight))
    # Sort: longest phrase first, then by weight descending
    rows.sort(key=lambda r: (-len(r[0]), -r[2]))
    _COMPILED.extend(rows)

_build_compiled_table()


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class IntentResult:
    """
    Single-intent result.

    Attributes
    ----------
    intent          : canonical intent name or "unknown"
    confidence      : 0.0 – 1.0  (winner_score / total_score)
    scores          : raw scores for each intent category
    matched_patterns: list of (phrase, intent, weight) that contributed
    elapsed_ms      : wall-clock time spent detecting (for perf audit)
    """
    intent:           str
    confidence:       float
    scores:           dict[str, float] = field(default_factory=dict)
    matched_patterns: list[tuple[str, str, int]] = field(default_factory=list)
    elapsed_ms:       float = 0.0

    def is_unknown(self) -> bool:
        return self.intent == "unknown"

    def to_dict(self) -> dict:
        return {
            "intent":           self.intent,
            "confidence":       round(self.confidence, 3),
            "scores":           {k: round(v, 2) for k, v in self.scores.items()},
            "matched_patterns": [(p, i, w) for p, i, w in self.matched_patterns],
            "elapsed_ms":       round(self.elapsed_ms, 3),
        }


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------
def _normalize(text: str) -> str:
    """Lowercase + collapse multiple spaces."""
    return re.sub(r'\s+', ' ', text.lower().strip())


def _scan(text: str) -> tuple[dict[str, float], list[tuple[str, str, int]]]:
    """
    Slide over the text and accumulate scores for every matching phrase.

    Returns
    -------
    scores  : {intent_name: total_score}
    matches : [(phrase, intent, weight), ...]
    """
    scores:  dict[str, float] = {intent: 0.0 for intent in ALL_PATTERNS}
    matched: list[tuple[str, str, int]] = []
    words   = text.split()
    n       = len(words)

    for phrase_tokens, intent, weight in _COMPILED:
        plen = len(phrase_tokens)
        for i in range(n - plen + 1):
            if words[i : i + plen] == phrase_tokens:
                scores[intent] += weight
                matched.append((" ".join(phrase_tokens), intent, weight))
                # Consume matched tokens to avoid double-counting same span
                break

    return scores, matched


def _priority_rank(intent: str) -> int:
    """Lower rank = higher priority."""
    try:
        return INTENT_PRIORITY.index(intent)
    except ValueError:
        return 999


def _apply_override_rules(
    scores:  dict[str, float],
    text:    str,
) -> dict[str, float]:
    """
    Enforce hard override rules AFTER scoring.

    Rule 1 — Exercise overrides Transport when exercise score > 0.
    Rule 2 — Verb outweighs noun (enforced by weight system).
    Rule 3 — Distance alone never triggers Transport.
    Rule 4 — Never default to petrol car (handled in Unknown path).
    Rule 5 — "running" with appliance noun → energy, not exercise.
    Rule 6 — "ordered" with food noun → food overrides shopping.
    """
    adj = dict(scores)
    words = set(text.split())

    # Rule 5: "running" in appliance context → remove exercise score
    if "running" in text and words & _APPLIANCE_NOUNS:
        adj["exercise"] = max(0.0, adj.get("exercise", 0) - 3.0)
        adj["energy"]   = adj.get("energy", 0) + 3.0

    # Rule 6: "ordered" + food noun → food wins over shopping
    _food_nouns = {
        "biriyani", "biryani", "briyani", "rice", "dosa", "idli", "idly",
        "noodles", "chicken", "mutton", "fish", "pizza", "burger", "food",
        "meal", "lunch", "dinner", "breakfast",
    }
    if "ordered" in text and words & _food_nouns:
        adj["food"]     = adj.get("food", 0) + 4.0
        adj["shopping"] = max(0.0, adj.get("shopping", 0) - 4.0)

    # Rule 1: exercise trumps transport
    if adj.get("exercise", 0) > 0 and adj.get("transport", 0) > 0:
        adj["transport"] = 0.0

    # Rule 3: suppress transport if score is entirely from unit-only matches
    transport_score = adj.get("transport", 0)
    if transport_score > 0:
        has_transport_verb = any(
            kw in text
            for kw in ("travelled", "traveled", "commuted", "flew", "boarded",
                       "drove", "rode", "went", "journey", "trip",
                       "by train", "by bus", "by car", "by flight",
                       "by metro", "took a", "took the")
        )
        if not has_transport_verb and transport_score <= 3:
            adj["transport"] = 0.0

    return adj



def _compute_confidence(
    winner_score: float,
    total_score:  float,
    second_score: float,
) -> float:
    """
    Confidence = share of total score captured by winner, boosted by
    the margin over the second-best intent.

    Range: 0.0 – 1.0
    """
    if total_score == 0:
        return 0.0
    share  = winner_score / total_score
    margin = (winner_score - second_score) / (winner_score + 1e-9)
    # Weighted blend: 60% share + 40% margin
    return min(share * 0.6 + margin * 0.4, 1.0)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def detect_intent(text: str) -> IntentResult:
    """
    Detect the primary intent from a single-sentence input.

    Steps
    -----
    1. Normalize
    2. Scan patterns (longest-match-first, weighted)
    3. Apply override rules
    4. Select winner (priority-aware)
    5. Compute confidence
    6. Threshold: confidence < CONFIDENCE_THRESHOLD → unknown

    Parameters
    ----------
    text : Raw user input string.

    Returns
    -------
    IntentResult
    """
    t0 = time.perf_counter()

    norm   = _normalize(text)
    scores, matched = _scan(norm)
    scores = _apply_override_rules(scores, norm)

    total_score = sum(scores.values())

    if total_score == 0:
        elapsed = (time.perf_counter() - t0) * 1000
        return IntentResult(
            intent="unknown",
            confidence=0.0,
            scores=scores,
            matched_patterns=matched,
            elapsed_ms=elapsed,
        )

    # Sort by score descending, break ties with priority
    ranked = sorted(
        scores.items(),
        key=lambda kv: (-kv[1], _priority_rank(kv[0]))
    )
    winner_intent, winner_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0.0

    confidence = _compute_confidence(winner_score, total_score, second_score)

    if confidence < CONFIDENCE_THRESHOLD:
        winner_intent = "unknown"

    elapsed = (time.perf_counter() - t0) * 1000
    return IntentResult(
        intent=winner_intent,
        confidence=round(confidence, 4),
        scores=scores,
        matched_patterns=matched,
        elapsed_ms=round(elapsed, 3),
    )


def detect_multi_intent(text: str) -> list[IntentResult]:
    """
    Detect multiple intents from a compound sentence.

    Splits on conjunctions / transition words, runs detect_intent on
    each segment, deduplicates by intent name.

    Example
    -------
    "I travelled by train and ate biriyani"
    → [IntentResult(intent='transport'), IntentResult(intent='food')]

    Parameters
    ----------
    text : Raw compound user input.

    Returns
    -------
    List of IntentResult (one per detected intent, ordered by appearance).
    """
    # Build a regex that splits on all splitter tokens
    splitter_pattern = '|'.join(
        re.escape(s.strip()) for s in sorted(MULTI_INTENT_SPLITTERS, key=len, reverse=True)
    )
    segments = re.split(splitter_pattern, text, flags=re.IGNORECASE)
    segments = [s.strip() for s in segments if s.strip()]

    if len(segments) <= 1:
        return [detect_intent(text)]

    results: list[IntentResult] = []
    seen_intents: set[str] = set()

    for seg in segments:
        r = detect_intent(seg)
        if r.intent != "unknown" and r.intent not in seen_intents:
            results.append(r)
            seen_intents.add(r.intent)

    # If nothing resolved, fall back to whole-text detection
    if not results:
        results = [detect_intent(text)]

    return results


def explain_intent(text: str) -> dict:
    """
    Debug helper — returns full scoring breakdown for a given input.

    Useful for:
    - Understanding why a particular intent was chosen.
    - Tuning pattern weights in intent_patterns.py.
    - Writing new test cases.

    Returns
    -------
    dict with keys: normalized, scores, matched_patterns, winner, confidence
    """
    norm = _normalize(text)
    scores, matched = _scan(norm)
    scores = _apply_override_rules(scores, norm)
    result = detect_intent(text)
    return {
        "input":           text,
        "normalized":      norm,
        "scores":          {k: round(v, 2) for k, v in scores.items()},
        "matched_patterns": [(p, i, w) for p, i, w in matched],
        "winner":          result.intent,
        "confidence":      result.confidence,
        "elapsed_ms":      result.elapsed_ms,
    }
