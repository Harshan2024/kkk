import threading

class ObservabilityMetrics:
    def __init__(self):
        self._lock = threading.Lock()
        self.db_retries = 0
        self.rate_limit_hits = 0
        self.timeouts = 0
        self.circuit_breaker_opens = 0
        self.service_failures = 0
        self.degraded_mode_activations = 0

    def increment(self, name: str):
        with self._lock:
            if hasattr(self, name):
                setattr(self, name, getattr(self, name) + 1)

    def get_metrics(self) -> dict:
        with self._lock:
            return {
                "db_retries": self.db_retries,
                "rate_limit_hits": self.rate_limit_hits,
                "timeouts": self.timeouts,
                "circuit_breaker_opens": self.circuit_breaker_opens,
                "service_failures": self.service_failures
            }

obs_metrics = ObservabilityMetrics()
