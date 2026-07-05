import time
import asyncio
import functools
from app.utils.logger import log_structured

class CircuitBreakerOpenException(Exception):
    pass

class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN
        self.last_state_change = time.time()

    def trip(self):
        self.state = "OPEN"
        self.last_state_change = time.time()

    def check_state(self):
        now = time.time()
        if self.state == "OPEN":
            if now - self.last_state_change > self.recovery_timeout:
                self.state = "HALF-OPEN"
                self.last_state_change = now
                log_structured("INFO", "circuit_breaker", f"Circuit Breaker '{self.name}' entered HALF-OPEN state.")
            else:
                raise CircuitBreakerOpenException(f"Circuit Breaker '{self.name}' is OPEN.")

    def record_success(self):
        if self.state == "HALF-OPEN":
            self.state = "CLOSED"
            self.failure_count = 0
            self.last_state_change = time.time()
            log_structured("INFO", "circuit_breaker", f"Circuit Breaker '{self.name}' recovered to CLOSED state.")

    def record_failure(self):
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.trip()
            log_structured("CRITICAL", "circuit_breaker", f"Circuit Breaker '{self.name}' tripped to OPEN state. Failure count: {self.failure_count}")

    def decorator(self, func):
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                self.check_state()
                try:
                    res = await func(*args, **kwargs)
                    self.record_success()
                    return res
                except Exception as e:
                    self.record_failure()
                    raise e
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                self.check_state()
                try:
                    res = func(*args, **kwargs)
                    self.record_success()
                    return res
                except Exception as e:
                    self.record_failure()
                    raise e
            return sync_wrapper


def retry_transient(max_retries: int = 3, base_delay: float = 1.0):
    def decorator(func):
        is_async = asyncio.iscoroutinefunction(func)
        
        def is_transient_error(e) -> bool:
            err_msg = str(e).lower()
            # Connection dropouts, DB OperationalError, timeouts, HTTP 502/503/504
            if any(x in err_msg for x in [
                "connection reset", "connection aborted", "timeout", 
                "server closed", "closed connection", "is closed",
                "502", "503", "504", "gateway", "service unavailable",
                "operationalerror", "connection refused", "handshake"
            ]):
                return True
            # Check explicit HTTP status codes
            if hasattr(e, "status_code"):
                if getattr(e, "status_code") in [502, 503, 504]:
                    return True
            return False

        if is_async:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                for attempt in range(1, max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        if is_transient_error(e) and attempt < max_retries:
                            delay = base_delay * (2 ** (attempt - 1))
                            log_structured("WARNING", "retry_transient", f"Transient error: {e}. Retrying async in {delay:.1f}s (Attempt {attempt}/{max_retries})...")
                            await asyncio.sleep(delay)
                        else:
                            raise e
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                for attempt in range(1, max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        if is_transient_error(e) and attempt < max_retries:
                            delay = base_delay * (2 ** (attempt - 1))
                            log_structured("WARNING", "retry_transient", f"Transient error: {e}. Retrying sync in {delay:.1f}s (Attempt {attempt}/{max_retries})...")
                            time.sleep(delay)
                        else:
                            raise e
            return sync_wrapper
    return decorator
