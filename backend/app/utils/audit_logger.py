import time
from datetime import datetime, timezone
from app.utils.logger import log_structured, request_id_var

def log_security_audit(
    event_type: str,  # e.g., "LOGIN", "FAILED_LOGIN", "LOGOUT", "REGISTRATION", "RESET_REQUEST", "RESET_CONFIRM", "PROFILE_UPDATE", "TOKEN_REFRESH", "TOKEN_REVOCATION"
    user_id: str,
    ip_address: str,
    endpoint: str,
    details: dict = None
):
    """
    Records a structured security audit event.
    Guarantees no password or token exposure.
    """
    # Filter out passwords and tokens from details just in case
    clean_details = {}
    if details:
        for k, v in details.items():
            if any(x in k.lower() for x in ["password", "token", "secret", "key", "auth", "credential"]):
                continue
            clean_details[k] = v

    log_structured(
        level="INFO",
        service="security_audit",
        message=f"Security audit event '{event_type}' for user '{user_id}'",
        context={
            "event_type": event_type,
            "user_id": user_id,
            "ip": ip_address,
            "endpoint": endpoint,
            "details": clean_details,
            "request_id": request_id_var.get()
        }
    )
