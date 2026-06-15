import time
import logging
from typing import Dict, List, Any

from app.utils.logger import log_structured

class StructuredLoggerWrapper:
    def __init__(self, service_name: str):
        self.service_name = service_name
    def info(self, msg: str):
        log_structured("INFO", self.service_name, msg)
    def warning(self, msg: str):
        log_structured("WARNING", self.service_name, msg)
    def error(self, msg: str):
        import sys
        _, exc, _ = sys.exc_info()
        log_structured("ERROR", self.service_name, msg, exception=exc)
    def critical(self, msg: str):
        log_structured("CRITICAL", self.service_name, msg)

logger = StructuredLoggerWrapper("ai_observability")

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
    Disabled during stabilization sprint.
    """
    pass

def track_confidence(score: float):
    """
    Disabled during stabilization sprint.
    """
    pass

def track_correction():
    """
    Disabled during stabilization sprint.
    """
    pass

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
