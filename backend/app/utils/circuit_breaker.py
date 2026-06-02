import time
from typing import Callable, Any

class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 3, recovery_timeout: float = 15.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN

    def call(self, func: Callable, *args, **kwargs) -> Any:
        now = time.time()
        
        # Check if OPEN circuit should transition to HALF-OPEN
        if self.state == "OPEN":
            if now - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF-OPEN"
                from app.utils.logger import log_structured_error
                log_structured_error(
                    service=f"circuit_breaker:{self.name}",
                    severity="info",
                    message=f"Circuit breaker '{self.name}' transitioned to HALF-OPEN. Attempting test call."
                )
            else:
                raise RuntimeError(f"Circuit breaker '{self.name}' is OPEN. Service is temporarily offline.")
                
        try:
            res = func(*args, **kwargs)
            # If successful and was HALF-OPEN, close the circuit
            if self.state == "HALF-OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
                from app.utils.logger import log_structured_error
                log_structured_error(
                    service=f"circuit_breaker:{self.name}",
                    severity="info",
                    message=f"Circuit breaker '{self.name}' successfully recovered and transitioned to CLOSED."
                )
            return res
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = now
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                from app.utils.logger import log_structured_error
                log_structured_error(
                    service=f"circuit_breaker:{self.name}",
                    severity="critical",
                    message=f"Circuit breaker '{self.name}' is now OPEN after {self.failure_count} consecutive failures.",
                    error=e
                )
            raise e

# Pre-defined breakers for AI services
breakers = {
    "embeddings": CircuitBreaker("embeddings", failure_threshold=3, recovery_timeout=15.0),
    "ocr": CircuitBreaker("ocr", failure_threshold=3, recovery_timeout=15.0),
    "recommendations": CircuitBreaker("recommendations", failure_threshold=3, recovery_timeout=15.0),
    "forecast": CircuitBreaker("forecast", failure_threshold=3, recovery_timeout=15.0),
}
