from typing import List, Dict, Any

def rank_recommendations(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ranks recommendations dynamically based on a weighted priority score:
    - impact_value (normalized): weight 25%
    - feasibility (HIGH=3, MEDIUM=1.5, LOW=0.5): weight 25%
    - difficulty (EASY=3, MEDIUM=1.5, HARD=0.5): weight 15%
    - sustainability_gain (normalized): weight 15%
    - confidence_score: weight 10%
    - behavioral_compatibility (normalized): weight 10%
    """
    if not candidates:
        return []
        
    # Find max values for normalization
    max_impact = max(c.get("impact_value", 1.0) for c in candidates)
    if max_impact == 0:
        max_impact = 1.0
        
    max_gain = max(c.get("sustainability_gain", 1.0) for c in candidates)
    if max_gain == 0:
        max_gain = 1.0
        
    max_compat = max(c.get("behavioral_compatibility", 1.0) for c in candidates)
    if max_compat == 0:
        max_compat = 1.0
        
    ranked = []
    for c in candidates:
        # Normalized scores between 0.0 and 3.0
        impact_norm = (c.get("impact_value", 0.0) / max_impact) * 3.0
        gain_norm = (c.get("sustainability_gain", 0.0) / max_gain) * 3.0
        compat_norm = (c.get("behavioral_compatibility", 0.0) / max_compat) * 3.0
        
        # Feasibility score
        feas_str = c.get("feasibility", "HIGH").upper()
        feas_val = 3.0 if feas_str == "HIGH" else 1.5 if feas_str == "MEDIUM" else 0.5
        
        # Difficulty score (EASY gets highest priority points)
        diff_str = c.get("difficulty", "EASY").upper()
        diff_val = 3.0 if diff_str == "EASY" else 1.5 if diff_str == "MEDIUM" else 0.5
        
        # Confidence score
        conf_val = c.get("confidence_score", 0.90) * 3.0
        
        # Weighted Priority Score calculation (Max possible score is 3.0)
        weighted_score = (
            (impact_norm * 0.25) + 
            (feas_val * 0.25) + 
            (diff_val * 0.15) + 
            (gain_norm * 0.15) + 
            (conf_val * 0.10) + 
            (compat_norm * 0.10)
        )
        
        # Create a copy with the calculated score
        c_copy = dict(c)
        c_copy["weighted_priority_score"] = round(weighted_score, 2)
        ranked.append(c_copy)
        
    # Sort descending by priority score
    ranked.sort(key=lambda x: x["weighted_priority_score"], reverse=True)
    return ranked
