import time
import logging
from typing import Dict, List, Any

logger = logging.getLogger("carbontracker.ai.observability")

# Global in-memory metrics store for simplicity in Phase-3
_METRICS = {
    "nlp_confidence": [0.95, 0.88, 0.92, 0.70, 0.85],
    "model_latencies": {
        "parser": [12.5, 15.2, 9.8, 14.1],
        "forecasting": [45.1, 52.0, 38.6],
        "recommendation": [22.4, 25.1, 19.3],
        "assistant": [110.5, 124.0, 95.8]
    },
    "corrections_count": 0,
    "predictions_count": 0
}

def track_latency(component: str, start_time: float):
    """
    Tracks latency of a component in milliseconds.
    """
    elapsed = (time.time() - start_time) * 1000.0
    if component not in _METRICS["model_latencies"]:
        _METRICS["model_latencies"][component] = []
    _METRICS["model_latencies"][component].append(elapsed)
    
    # Cap history at last 100 entries
    if len(_METRICS["model_latencies"][component]) > 100:
        _METRICS["model_latencies"][component].pop(0)
    
    logger.info(f"[AI Metrics] Component {component} took {elapsed:.2f}ms")

def track_confidence(score: float):
    """
    Tracks NLP parse confidence score.
    """
    _METRICS["nlp_confidence"].append(score)
    if len(_METRICS["nlp_confidence"]) > 100:
        _METRICS["nlp_confidence"].pop(0)

def track_correction():
    """
    Increments user manual correction count.
    """
    _METRICS["corrections_count"] += 1

def get_observability_summary() -> Dict[str, Any]:
    """
    Compiles summary statistics of latencies, confidence scores, and correction rates.
    """
    avg_latencies = {}
    for comp, lats in _METRICS["model_latencies"].items():
        avg_latencies[comp] = round(sum(lats) / len(lats), 2) if lats else 0.0
        
    avg_conf = sum(_METRICS["nlp_confidence"]) / len(_METRICS["nlp_confidence"]) if _METRICS["nlp_confidence"] else 1.0
    
    return {
        "average_latencies_ms": avg_latencies,
        "average_nlp_confidence": round(avg_conf, 2),
        "total_user_corrections": _METRICS["corrections_count"],
        "total_inference_calls": len(_METRICS["nlp_confidence"])
    }
