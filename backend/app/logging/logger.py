import logging
import sys
import time
from typing import Callable, Any
from app.utils.logger import log_structured

def configure_logging(level: int = logging.INFO):
    """
    Sets up application-wide logger formatters and handlers.
    """
    logger = logging.getLogger("carbontracker")
    logger.setLevel(level)
    
    # Avoid duplicate handlers if reloaded
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        # Output pure JSON messages for log collectors in production
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

def get_logger(module_name: str) -> logging.Logger:
    """
    Returns a child logger for modular tracking.
    """
    return logging.getLogger(f"carbontracker.{module_name}")

def log_api_latency(endpoint: str, start_time: float):
    """
    Helper to log request execution latency.
    """
    elapsed = (time.time() - start_time) * 1000.0
    log_structured(
        level="INFO",
        service="api_latency",
        message=f"Endpoint {endpoint} resolved in {elapsed:.2f}ms",
        context={"endpoint": endpoint, "elapsed_ms": elapsed}
    )

