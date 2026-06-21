"""
debug_waste_trace.py
====================
CarbonTracker AI - Debug Trace for Waste Entity Extraction

Input: "I recycled 1 kg electronic waste"

Traces EVERY layer of the pipeline:
  Layer 1: Intent Detection
  Layer 2: Raw Entity Extraction (entity_engine)
  Layer 3: Alias / Factor Mapping (waste_factors lookup)
  Layer 4: Weight Extraction (waste_carbon_engine internal)
  Layer 5: Waste Carbon Engine Input
  Layer 6: Final Carbon Calculation

NO CODE IS MODIFIED.  Read-only trace only.
"""

import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

INPUT_TEXT = "I recycled 1 kg electronic waste"

SEP = "=" * 65

def pprint(title, data):
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)
    if isinstance(data, dict):
        print(json.dumps({str(k): str(v) for k, v in data.items()}, indent=4))
    elif isinstance(data, str):
        print(f"  {data}")
    else:
        print(f"  {data!r}")

print(f"\n{'#' * 65}")
print(f"  WASTE ENTITY EXTRACTION - COMPLETE PIPELINE TRACE")
print(f"  Input: \"{INPUT_TEXT}\"")
print(f"{'#' * 65}")


# =============================================================================
# LAYER 1: Intent Detection
# =============================================================================
from app.nlp.intent_engine import detect_intent

intent_result = detect_intent(INPUT_TEXT)

pprint("LAYER 1: INTENT DETECTION", {
    "intent":            intent_result.intent,
    "confidence":        round(intent_result.confidence, 4),
    "elapsed_ms":        round(intent_result.elapsed_ms, 3),
    "matched_patterns":  intent_result.matched_patterns,
    "all_scores":        dict(intent_result.scores),
})

print(f"\n  >> Intent detected: \"{intent_result.intent}\"")
intent_ok = intent_result.intent == "waste"
print(f"  >> Expected: \"waste\"  --  {'[CORRECT]' if intent_ok else '[WRONG - PIPELINE DIVERTS HERE]'}")


# =============================================================================
# LAYER 2: Raw Entity Extraction (entity_engine)
# =============================================================================
from app.nlp.entity_engine import extract_entities

entity_result = extract_entities(INPUT_TEXT, intent="waste")

pprint("LAYER 2: RAW ENTITY EXTRACTION (entity_engine)", entity_result)

entity_raw = entity_result.get("entity", "NOT FOUND")
waste_type_raw = entity_result.get("waste_type", "NOT FOUND")
weight_raw = entity_result.get("weight", "NOT FOUND")
unit_raw = entity_result.get("unit", "NOT FOUND")

print(f"\n  >> entity:     {entity_raw!r}")
print(f"  >> waste_type: {waste_type_raw!r}")
print(f"  >> weight:     {weight_raw!r}")
print(f"  >> unit:       {unit_raw!r}")
entity_ok = "electronic" in str(entity_raw).lower() or "e-waste" in str(entity_raw).lower() or "e_waste" in str(entity_raw).lower()
print(f"  >> Entity contains 'electronic' or 'e-waste': {'[CORRECT]' if entity_ok else '[WRONG - ENTITY MAPPING ISSUE HERE]'}")


# =============================================================================
# LAYER 3: Alias / Factor Lookup (waste_factors)
# =============================================================================
from app.carbon.waste_factors import lookup_waste_from_text, WASTE_ALIASES, WASTE_FACTORS

factor_match = lookup_waste_from_text(INPUT_TEXT)

pprint("LAYER 3: ALIAS / FACTOR MAPPING (waste_factors.lookup_waste_from_text)", factor_match or {"result": "None — no match found"})

if factor_match:
    print(f"\n  >> keyword_matched: {factor_match['keyword_matched']!r}")
    print(f"  >> canonical_key:   {factor_match['canonical_key']!r}")
    print(f"  >> display_name:    {factor_match['display_name']!r}")
    print(f"  >> factor:          {factor_match['factor']!r}")
    alias_ok = factor_match["display_name"] == "E-Waste"
    print(f"  >> display_name == 'E-Waste': {'[CORRECT]' if alias_ok else '[WRONG - ALIAS NOT RESOLVING]'}")
    print(f"\n  ALIAS TABLE ENTRY CHECK:")
    alias_entry = WASTE_ALIASES.get("electronic waste")
    print(f"    WASTE_ALIASES['electronic waste'] -> {alias_entry!r}  {'[FOUND]' if alias_entry else '[MISSING IN ALIAS TABLE]'}")
    print(f"    WASTE_FACTORS['{alias_entry}'] -> {WASTE_FACTORS.get(alias_entry)!r}")
else:
    print(f"\n  >> [ERROR] No waste match found in waste_factors.")
    print(f"\n  ALIAS TABLE CHECK — scanning for 'electronic waste':")
    for k, v in WASTE_ALIASES.items():
        if "electronic" in k:
            print(f"    Found alias: '{k}' -> '{v}'")


# =============================================================================
# LAYER 4: Weight Extraction (waste_carbon_engine internal)
# =============================================================================
# Call the private weight extractor directly (read-only, no modification)
from app.carbon.waste_carbon_engine import _extract_weight_from_text

weight_info = _extract_weight_from_text(INPUT_TEXT)

pprint("LAYER 4: WEIGHT EXTRACTION (_extract_weight_from_text)", weight_info or {"result": "None — no weight found"})

if weight_info:
    print(f"\n  >> original_value: {weight_info['original_value']!r}")
    print(f"  >> original_unit:  {weight_info['original_unit']!r}")
    print(f"  >> weight_kg:      {weight_info['weight_kg']!r}")
    weight_ok = weight_info["weight_kg"] == 1.0
    print(f"  >> weight_kg == 1.0: {'[CORRECT]' if weight_ok else '[WRONG]'}")
else:
    print(f"\n  >> [ERROR] Weight extraction returned None.")


# =============================================================================
# LAYER 5: Waste Carbon Engine — Full Input Summary
# =============================================================================
pprint("LAYER 5: WASTE CARBON ENGINE INPUT SUMMARY", {
    "text_input":      INPUT_TEXT,
    "waste_entity":    factor_match["display_name"] if factor_match else "NOT RESOLVED",
    "canonical_key":   factor_match["canonical_key"] if factor_match else "NOT RESOLVED",
    "factor":          factor_match["factor"] if factor_match else "NOT FOUND",
    "weight_kg":       weight_info["weight_kg"] if weight_info else "NOT FOUND",
    "original_value":  weight_info["original_value"] if weight_info else "NOT FOUND",
    "original_unit":   weight_info["original_unit"] if weight_info else "NOT FOUND",
})


# =============================================================================
# LAYER 6: Final Carbon Calculation
# =============================================================================
from app.carbon.waste_carbon_engine import calculate_waste_carbon_from_text
from app.carbon.waste_formula import calculate_waste_carbon, format_waste_formula

final_result = calculate_waste_carbon_from_text(INPUT_TEXT)

pprint("LAYER 6: FINAL CARBON CALCULATION (calculate_waste_carbon_from_text)", final_result)

if "error" not in final_result:
    weight_used = final_result.get("weight")
    factor_used = final_result.get("factor")
    formula_str = final_result.get("formula")
    carbon_out  = final_result.get("carbon")
    waste_type  = final_result.get("waste_type")

    print(f"\n  >> waste_type: {waste_type!r}")
    print(f"  >> weight:     {weight_used!r} kg")
    print(f"  >> factor:     {factor_used!r}")
    print(f"  >> formula:    {formula_str!r}")
    print(f"  >> carbon:     {carbon_out!r} kg CO2")

    expected_co2 = 12.0
    final_ok = carbon_out == expected_co2
    entity_display_ok = waste_type == "E-Waste"
    print(f"\n  >> carbon == 12.0:          {'[CORRECT]' if final_ok else '[WRONG]'}")
    print(f"  >> waste_type == 'E-Waste': {'[CORRECT]' if entity_display_ok else '[WRONG]'}")
else:
    print(f"\n  >> [ERROR] Engine returned: {final_result}")


# =============================================================================
# PIPELINE SUMMARY TRACE
# =============================================================================
print(f"\n{'#' * 65}")
print(f"  PIPELINE TRACE SUMMARY")
print(f"  Input: \"{INPUT_TEXT}\"")
print(f"{'#' * 65}")

stages = [
    ("Intent Detection",        intent_result.intent,                                  "waste"),
    ("Entity (raw)",            str(entity_result.get("entity", "?")),                 "electronic_waste or e_waste"),
    ("Alias -> canonical",      factor_match["canonical_key"] if factor_match else "?","e-waste"),
    ("Display Name",            factor_match["display_name"] if factor_match else "?", "E-Waste"),
    ("Factor",                  str(factor_match["factor"]) if factor_match else "?",  "12.0"),
    ("Weight (kg)",             str(weight_info["weight_kg"]) if weight_info else "?", "1.0"),
    ("Formula",                 final_result.get("formula", "?"),                      "1 x 12.0"),
    ("Final Carbon (kg CO2)",   str(final_result.get("carbon", "?")),                  "12.0"),
    ("Display Entity",          str(final_result.get("waste_type", "?")),              "E-Waste"),
]

print(f"\n  {'Stage':<30} {'Actual':<25} {'Expected':<20} Status")
print(f"  {'-'*90}")
for stage, actual, expected in stages:
    match = str(actual).lower() == str(expected).lower() or str(actual) == str(expected)
    status = "[OK]" if match else "[!! ISSUE !!]"
    print(f"  {stage:<30} {str(actual):<25} {expected:<20} {status}")

print(f"\n{'#' * 65}\n")
