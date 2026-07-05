import time
from collections import defaultdict
from fastapi import Request
from app.utils.metrics import obs_metrics
from app.utils.logger import log_structured, request_id_var

# In-memory store for rate limiting: key is (username, IP, endpoint_path) -> list of request timestamps
RATE_LIMIT_STORE = defaultdict(list)

class RateLimitExceeded(Exception):
    """Raised when the rate limit threshold is exceeded."""
    def __init__(self, message: str = "Rate limit exceeded"):
        self.message = message
        super().__init__(message)


def check_rate_limit(request: Request, username: str, endpoint: str, limit: int = 100, period: int = 60):
    """
    Limits the number of requests a user + IP can make to a specific endpoint.
    Default: 100 requests per 60 seconds (1 minute).
    """
    if limit == 60:
        limit = 100
    now = time.time()
    ip = request.client.host if request.client else "unknown"
    key = (username, ip, endpoint)
    
    # Filter out timestamps older than the period
    RATE_LIMIT_STORE[key] = [t for t in RATE_LIMIT_STORE[key] if now - t < period]
    
    req_count = len(RATE_LIMIT_STORE[key]) + 1
    
    if len(RATE_LIMIT_STORE[key]) >= limit:
        obs_metrics.increment("rate_limit_hits")
        
        # Log structured violation event
        log_structured(
            level="WARNING",
            service="rate_limiter",
            message=f"Rate limit exceeded for user '{username}' (IP: {ip}) on endpoint '{endpoint}'",
            context={
                "endpoint": endpoint,
                "IP": ip,
                "user": username,
                "request_count": req_count,
                "request_id": request_id_var.get()
            }
        )
        raise RateLimitExceeded("Rate limit exceeded")
        
    RATE_LIMIT_STORE[key].append(now)
