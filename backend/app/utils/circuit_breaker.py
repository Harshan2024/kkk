import time
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Callable, Any
from app.utils.logger import log_structured, request_id_var
from app.utils.metrics import obs_metrics

class CircuitBreakerOpenException(Exception):
    """Raised when a circuit breaker is in the OPEN state."""
    def __init__(self, name: str, message: str = "Service temporarily unavailable"):
        self.name = name
        super().__init__(message)


class CircuitBreaker:
    _executor = ThreadPoolExecutor(max_workers=20)

    def __init__(self, name: str, failure_threshold: int = 3, recovery_timeout: float = 15.0, call_timeout: float = 8.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.call_timeout = call_timeout
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN
        self._lock = threading.Lock()

    def call(self, func: Callable, *args, **kwargs) -> Any:
        now = time.time()
        
        with self._lock:
            # Check if OPEN circuit should transition to HALF-OPEN
            if self.state == "OPEN":
                if now - self.last_failure_time > self.recovery_timeout:
                    self.state = "HALF-OPEN"
                    log_structured(
                        level="INFO",
                        service=f"circuit_breaker:{self.name}",
                        message=f"Circuit breaker '{self.name}' transitioned to HALF-OPEN. Attempting test call."
                    )
                else:
                    if self.name == "ocr":
                        obs_metrics.increment("ocr_failures")
                    else:
                        obs_metrics.increment("ai_failures")
                    raise CircuitBreakerOpenException(self.name, "Service temporarily unavailable")

        # Execute func in executor with specified timeout
        future = self._executor.submit(func, *args, **kwargs)
        try:
            res = future.result(timeout=self.call_timeout)
            
            with self._lock:
                # If successful and was HALF-OPEN, close the circuit
                if self.state == "HALF-OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                    log_structured(
                        level="INFO",
                        service=f"circuit_breaker:{self.name}",
                        message=f"Circuit breaker '{self.name}' successfully recovered and transitioned to CLOSED."
                    )
            return res
        except Exception as e:
            is_timeout = isinstance(e, FutureTimeoutError)
            
            with self._lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                # Increment metrics
                if is_timeout:
                    obs_metrics.increment("timeouts")
                    log_structured(
                        level="WARNING",
                        service=f"circuit_breaker:{self.name}",
                        message=f"Timeout of {self.call_timeout}s occurred while calling {func.__name__} in circuit breaker '{self.name}'.",
                        exception=e
                    )
                else:
                    log_structured(
                        level="ERROR",
                        service=f"circuit_breaker:{self.name}",
                        message=f"Service call failed in circuit breaker '{self.name}': {e}",
                        exception=e
                    )
                
                if self.name == "ocr":
                    obs_metrics.increment("ocr_failures")
                else:
                    obs_metrics.increment("ai_failures")
                
                if self.failure_count >= self.failure_threshold and self.state != "OPEN":
                    self.state = "OPEN"
                    obs_metrics.increment("circuit_breaker_opens")
                    log_structured(
                        level="CRITICAL",
                        service=f"circuit_breaker:{self.name}",
                        message=f"Circuit breaker '{self.name}' is now OPEN after {self.failure_count} consecutive failures.",
                        context={"request_id": request_id_var.get()}
                    )
            
            raise CircuitBreakerOpenException(self.name, "Service temporarily unavailable")

# Pre-defined breakers for AI services with timeout specifications
breakers = {
    "embeddings": CircuitBreaker("embeddings", failure_threshold=3, recovery_timeout=15.0, call_timeout=8.0),
    "ocr": CircuitBreaker("ocr", failure_threshold=3, recovery_timeout=15.0, call_timeout=15.0),
    "recommendations": CircuitBreaker("recommendations", failure_threshold=3, recovery_timeout=15.0, call_timeout=8.0),
    "forecast": CircuitBreaker("forecast", failure_threshold=3, recovery_timeout=15.0, call_timeout=8.0),
    "semantic_search": CircuitBreaker("semantic_search", failure_threshold=3, recovery_timeout=15.0, call_timeout=8.0),
}
