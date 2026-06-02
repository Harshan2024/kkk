import time
from collections import defaultdict
from fastapi import HTTPException

# In-memory store for rate limiting: key is (username, endpoint_path) -> list of request timestamps
RATE_LIMIT_STORE = defaultdict(list)

def check_rate_limit(username: str, endpoint: str, limit: int = 60, period: int = 60):
    """
    Limits the number of requests a user can make to a specific endpoint.
    Default: 60 requests per 60 seconds (1 minute).
    """
    now = time.time()
    key = (username, endpoint)
    
    # Filter out timestamps older than the period
    RATE_LIMIT_STORE[key] = [t for t in RATE_LIMIT_STORE[key] if now - t < period]
    
    if len(RATE_LIMIT_STORE[key]) >= limit:
        from app.utils.logger import log_structured_error
        log_structured_error(
            service="rate_limiter",
            severity="warn",
            message=f"Rate limit exceeded for user '{username}' on endpoint '{endpoint}'"
        )
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait a minute before making another request."
        )
        
    RATE_LIMIT_STORE[key].append(now)
