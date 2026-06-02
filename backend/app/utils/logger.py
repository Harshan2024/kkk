import logging
import sys
import json
import traceback
from datetime import datetime

# Root logger for CarbonTracker
root_logger = logging.getLogger("carbontracker")

def log_structured_error(service: str, severity: str, message: str, error: Exception = None):
    """
    Logs structured error details containing timestamp, service, severity, message, and stack trace.
    Standardized for Fase-3 observability.
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    stack_trace = None
    if error:
        stack_trace = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    elif sys.exc_info()[0]:
        stack_trace = traceback.format_exc()
        
    log_entry = {
        "timestamp": timestamp,
        "service": service,
        "severity": severity.upper(),
        "message": message,
        "stack_trace": stack_trace
    }
    
    msg_str = json.dumps(log_entry)
    
    # Log to Python standard logging system
    if severity.lower() == "critical":
        root_logger.critical(msg_str)
    elif severity.lower() == "error":
        root_logger.error(msg_str)
    elif severity.lower() in ("warn", "warning"):
        root_logger.warning(msg_str)
    else:
        root_logger.info(msg_str)
