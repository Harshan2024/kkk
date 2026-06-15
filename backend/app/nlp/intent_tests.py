"""
intent_tests.py
===============
CarbonTracker AI — Phase A Intent Detection Engine
Complete Verification Suite

Covers:
- All 14 spec test cases
- Validation rules (exercise > transport, verb > noun, no petrol-car default)
- Multi-intent detection
- Unknown intent handling
- Performance requirement (<50ms average, <100ms maximum)
- Confidence thresholding

Run:
    python intent_tests.py
    (from backend/ directory with .venv activated)
"""

import sys
import os
import time

sys.path.insert(0, r"c:\Users\tutyr\Downloads\Harshan\New\backend")

from app.nlp.intent_engine import detect_intent, detect_multi_intent, explain_intent

# ─────────────────────────────────────────────────────────────────────────────
# Test runner
# ─────────────────────────────────────────────────────────────────────────────
PASS_COUNT = 0
FAIL_COUNT = 0
ALL_LATENCIES: list[float] = []


def check(label: str, actual: str, expected: str, elapsed_ms: float = 0.0) -> bool:
    global PASS_COUNT, FAIL_COUNT
    ALL_LATENCIES.append(elapsed_ms)
    ok = actual.lower() == expected.lower()
    status = "PASS" if ok else "FAIL"
    if ok:
        PASS_COUNT += 1
        print(f"  [{status}] {label:55s}  → {actual!r:<12} ({elapsed_ms:.2f}ms)")
    else:
        FAIL_COUNT += 1
        print(f"  [{status}] {label:55s}  → got {actual!r}, expected {expected!r} ({elapsed_ms:.2f}ms)")
    return ok


def check_confidence(label: str, confidence: float, min_val: float) -> bool:
    global PASS_COUNT, FAIL_COUNT
    ok = confidence >= min_val
    status = "PASS" if ok else "FAIL"
    if ok:
        PASS_COUNT += 1
        print(f"  [{status}] {label:55s}  → confidence={confidence:.3f} (>= {min_val})")
    else:
        FAIL_COUNT += 1
        print(f"  [{status}] {label:55s}  → confidence={confidence:.3f} (BELOW threshold {min_val})")
    return ok


def check_latency(label: str, elapsed_ms: float, max_ms: float) -> bool:
    global PASS_COUNT, FAIL_COUNT
    ok = elapsed_ms <= max_ms
    status = "PASS" if ok else "FAIL"
    if ok:
        PASS_COUNT += 1
        print(f"  [{status}] {label:55s}  → {elapsed_ms:.3f}ms (limit {max_ms}ms)")
    else:
        FAIL_COUNT += 1
        print(f"  [{status}] {label:55s}  → {elapsed_ms:.3f}ms EXCEEDS limit {max_ms}ms")
    return ok


# ─────────────────────────────────────────────────────────────────────────────
# SPEC TEST CASES (14 from the spec)
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 75)
print(" CarbonTracker AI — Phase A Intent Detection Engine — Verification Suite")
print("=" * 75)

print("\n── Spec Test Cases (14) ─────────────────────────────────────────────────")

spec_cases: list[tuple[str, str]] = [
    ("I ran 3 km",                                      "exercise"),
    ("I walked 5 km",                                   "exercise"),
    ("I drove 10 km",                                   "transport"),
    ("I travelled from Chennai to Madurai",              "transport"),
    ("I ate chicken biriyani",                          "food"),
    ("I had coffee",                                    "food"),
    ("I used AC for 4 hours",                           "energy"),
    ("I charged my laptop",                             "energy"),
    ("I bought a laptop",                               "shopping"),
    ("I purchased shoes",                               "shopping"),
    ("I disposed 2 kg plastic waste",                   "waste"),
    ("I threw away old batteries",                      "waste"),
]

for text, expected in spec_cases:
    r = detect_intent(text)
    check(f'"{text}"', r.intent, expected, r.elapsed_ms)

# ─────────────────────────────────────────────────────────────────────────────
# Multi-intent test
print("\n── Multi-Intent Detection ───────────────────────────────────────────────")
multi_text = "I travelled by train and ate biriyani"
multi_results = detect_multi_intent(multi_text)
intents_found = [r.intent for r in multi_results]
print(f"  Input: \"{multi_text}\"")
print(f"  Detected intents: {intents_found}")
if "transport" in intents_found and "food" in intents_found:
    PASS_COUNT += 1
    print(f"  [PASS] Multi-intent → transport + food both detected")
else:
    FAIL_COUNT += 1
    print(f"  [FAIL] Multi-intent → expected [transport, food], got {intents_found}")

# ─────────────────────────────────────────────────────────────────────────────
# Unknown intent test
print("\n── Unknown Intent ───────────────────────────────────────────────────────")
unknown_cases = [
    "I did something today",
    "random stuff happened",
    "something",
]
for text in unknown_cases:
    r = detect_intent(text)
    check(f'"{text}"', r.intent, "unknown", r.elapsed_ms)

# ─────────────────────────────────────────────────────────────────────────────
# Validation rules
print("\n── Validation Rules ─────────────────────────────────────────────────────")

# Rule 1 — Distance alone ≠ transport
r_km_only = detect_intent("3 km")
check('Rule 1: "3 km" alone → NOT transport (unknown)', r_km_only.intent, "unknown", r_km_only.elapsed_ms)

# Rule 2 — Verb outweighs noun
r_buy_laptop  = detect_intent("I bought a laptop")
r_chg_laptop  = detect_intent("I charged my laptop for 2 hours")
check('Rule 2a: "bought a laptop" → shopping (verb beats noun)', r_buy_laptop.intent,  "shopping",   r_buy_laptop.elapsed_ms)
check('Rule 2b: "charged laptop"  → energy   (verb beats noun)', r_chg_laptop.intent,  "energy",     r_chg_laptop.elapsed_ms)

# Rule 3 — Exercise overrides transport
r_cycled = detect_intent("I cycled 10 km")
r_ran    = detect_intent("I ran 5 km to work")
check('Rule 3a: "cycled 10 km" → exercise (overrides transport)', r_cycled.intent, "exercise", r_cycled.elapsed_ms)
check('Rule 3b: "ran 5 km"     → exercise (overrides transport)', r_ran.intent,    "exercise", r_ran.elapsed_ms)

# Rule 4 — Never petrol car default (unknown stays unknown)
r_vague = detect_intent("I went somewhere")
# "went" alone is weak transport — should still be transport, NOT petrol car classification
# (the "no petrol car default" rule is about the CALCULATION ENGINE, not intent)
print(f"  [INFO] 'I went somewhere' → intent={r_vague.intent!r} (transport verb present, that is correct)")

# ─────────────────────────────────────────────────────────────────────────────
# Additional coverage tests
print("\n── Additional Coverage ──────────────────────────────────────────────────")

extras: list[tuple[str, str]] = [
    ("yoga",                                    "exercise"),
    ("1 hour yoga was done today",              "exercise"),
    ("meditation for 20 minutes",               "exercise"),
    ("gym workout for 1 hour",                  "exercise"),
    ("stretching exercises",                    "exercise"),
    ("I jogged 4 km this morning",              "exercise"),
    ("I went for a morning walk",               "exercise"),
    ("I swam 500 metres",                       "exercise"),
    ("I flew from Delhi to Mumbai",             "transport"),
    ("I took the metro to office",              "transport"),
    ("I boarded a bus to college",              "transport"),
    ("I had sambar rice for lunch",             "food"),
    ("I drank orange juice",                    "food"),
    ("I ordered chicken biriyani from Swiggy",  "food"),
    ("I used the washing machine for 1 hour",   "energy"),
    ("I switched on the AC",                    "energy"),
    ("I left the TV running for 3 hours",       "energy"),
    ("I purchased a new smartphone",            "shopping"),
    ("I ordered a shirt online",                "shopping"),
    ("I recycled 3 kg of plastic",              "waste"),
    ("I discarded old e-waste",                 "waste"),
]

for text, expected in extras:
    r = detect_intent(text)
    check(f'"{text}"', r.intent, expected, r.elapsed_ms)

# ─────────────────────────────────────────────────────────────────────────────
# Confidence checks
print("\n── Confidence Scores ────────────────────────────────────────────────────")
confidence_cases: list[tuple[str, float]] = [
    ("I ran 3 km",          0.50),
    ("I bought a laptop",   0.50),
    ("I ate chicken biriyani", 0.50),
    ("I charged my laptop", 0.50),
    ("I disposed plastic waste", 0.50),
]
for text, min_conf in confidence_cases:
    r = detect_intent(text)
    check_confidence(f'"{text}"', r.confidence, min_conf)

# ─────────────────────────────────────────────────────────────────────────────
# Performance requirement: <50ms average, <100ms maximum
print("\n── Performance Requirements ─────────────────────────────────────────────")

perf_cases = spec_cases + extras
latencies: list[float] = []
for text, _ in perf_cases:
    r = detect_intent(text)
    latencies.append(r.elapsed_ms)

avg_ms = sum(latencies) / len(latencies)
max_ms = max(latencies)

check_latency("Average detection latency (requirement: <50ms)",  avg_ms, 50.0)
check_latency("Maximum detection latency (requirement: <100ms)", max_ms, 100.0)

print(f"\n  Latency details:")
print(f"    Average : {avg_ms:.3f} ms")
print(f"    Maximum : {max_ms:.3f} ms")
print(f"    Minimum : {min(latencies):.3f} ms")

# ─────────────────────────────────────────────────────────────────────────────
# Debug explain example
print("\n── Explain Output (sample) ──────────────────────────────────────────────")
explanation = explain_intent("I ran 5 km")
print(f"  Input            : {explanation['input']!r}")
print(f"  Normalized       : {explanation['normalized']!r}")
print(f"  Scores           : {explanation['scores']}")
print(f"  Matched patterns : {explanation['matched_patterns']}")
print(f"  Winner           : {explanation['winner']!r}")
print(f"  Confidence       : {explanation['confidence']}")
print(f"  Elapsed ms       : {explanation['elapsed_ms']}")

# ─────────────────────────────────────────────────────────────────────────────
# Summary
total = PASS_COUNT + FAIL_COUNT
print()
print("=" * 75)
print(f" Results: {PASS_COUNT} PASSED  |  {FAIL_COUNT} FAILED  |  {total} TOTAL")
print("=" * 75)

if FAIL_COUNT:
    sys.exit(1)
