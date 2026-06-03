import logging
import sys
import json
import traceback
from datetime import datetime

import contextvars

# Setup root logger
root_logger = logging.getLogger("carbontracker")

# ContextVar to hold current request ID
request_id_var = contextvars.ContextVar("request_id", default="REQ-SYSTEM")

def log_structured(level: str, service: str, message: str, context: dict = None, exception: Exception = None):
    """
    Centralized logging function.
    Log structure: timestamp, service, level (severity), message, context, exception (if any), request_id.
    """
    timestamp = datetime.utcnow().isoformat()
    req_id = request_id_var.get()
    
    exc_str = None
    if exception:
        exc_str = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
    elif sys.exc_info()[0]:
        exc_str = traceback.format_exc()

    log_entry = {
        "timestamp": timestamp,
        "service": service,
        "level": level.upper(),
        "message": message,
        "context": context or {},
        "request_id": req_id
    }
    if exc_str:
        log_entry["exception"] = exc_str

    msg_str = json.dumps(log_entry)
    
    # Log to Python standard logging system
    if level.upper() == "CRITICAL":
        root_logger.critical(msg_str)
    elif level.upper() == "ERROR":
        root_logger.error(msg_str)
    elif level.upper() in ("WARN", "WARNING"):
        root_logger.warning(msg_str)
    else:
        root_logger.info(msg_str)

def log_structured_error(service: str, severity: str, message: str, error: Exception = None):
    """
    Legacy compatibility wrapper for log_structured.
    """
    log_structured(
        level=severity,
        service=service,
        message=message,
        exception=error
    )
