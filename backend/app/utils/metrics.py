"""
metrics.py — CarbonTracker Production Observability Metrics
============================================================
Thread-safe, in-process metrics collector.
Tracks API performance, error rates, cache ratios, and latency distributions.
"""

import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Dict, List, Optional

# ─── Latency Bucket Boundaries (ms) ──────────────────────────────────────────
LATENCY_BUCKETS = [10, 25, 50, 100, 250, 500, 1000, 2500, 5000]


class LatencyHistogram:
    """Per-endpoint latency histogram with p50/p95/p99 calculation."""

    def __init__(self, max_samples: int = 1000):
        self._lock = threading.Lock()
        self._samples: deque = deque(maxlen=max_samples)

    def record(self, ms: float):
        with self._lock:
            self._samples.append(ms)

    def percentile(self, p: float) -> Optional[float]:
        with self._lock:
            if not self._samples:
                return None
            sorted_s = sorted(self._samples)
            idx = max(0, int(len(sorted_s) * p / 100) - 1)
            return round(sorted_s[idx], 2)

    def avg(self) -> Optional[float]:
        with self._lock:
            if not self._samples:
                return None
            return round(sum(self._samples) / len(self._samples), 2)

    def count(self) -> int:
        with self._lock:
            return len(self._samples)

    def buckets(self) -> Dict[str, int]:
        """Returns count of samples falling in each latency bucket."""
        with self._lock:
            result: Dict[str, int] = {f"le_{b}ms": 0 for b in LATENCY_BUCKETS}
            result["le_inf"] = 0
            for ms in self._samples:
                placed = False
                for b in LATENCY_BUCKETS:
                    if ms <= b:
                        result[f"le_{b}ms"] += 1
                        placed = True
                        break
                if not placed:
                    result["le_inf"] += 1
            return result


class EndpointMetrics:
    """Per-endpoint counters and latency."""

    def __init__(self):
        self._lock = threading.Lock()
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        self.latency = LatencyHistogram()

    def record_request(self, status_code: int, duration_ms: float):
        with self._lock:
            self.request_count += 1
            if 200 <= status_code < 400:
                self.success_count += 1
            else:
                self.error_count += 1
        self.latency.record(duration_ms)

    def summary(self) -> dict:
        with self._lock:
            total = self.request_count
            error_rate = round((self.error_count / total * 100), 2) if total > 0 else 0.0
            success_rate = round((self.success_count / total * 100), 2) if total > 0 else 0.0
        return {
            "request_count": total,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "error_rate_pct": error_rate,
            "success_rate_pct": success_rate,
            "latency_p50_ms": self.latency.percentile(50),
            "latency_p95_ms": self.latency.percentile(95),
            "latency_p99_ms": self.latency.percentile(99),
            "latency_avg_ms": self.latency.avg(),
        }


class ObservabilityMetrics:
    """
    Central metrics registry for CarbonTracker AI.
    Thread-safe. Stores in-process counters for:
    - System-level error/reliability counters
    - Per-endpoint request/latency tracking
    - Cache hit/miss ratios
    - Background job tracking
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._start_time = time.time()

        # ── System-level counters ───────────────────────────────────────────
        self.db_retries = 0
        self.rate_limit_hits = 0
        self.timeouts = 0
        self.circuit_breaker_opens = 0
        self.ai_failures = 0
        self.ocr_failures = 0
        self.recovery_mode_activations = 0

        # ── Cache metrics ───────────────────────────────────────────────────
        self.cache_hits = 0
        self.cache_misses = 0

        # ── Background job counters ─────────────────────────────────────────
        self.bg_jobs_total = 0
        self.bg_jobs_success = 0
        self.bg_jobs_failed = 0

        # ── Auth event counters ─────────────────────────────────────────────
        self.logins_success = 0
        self.logins_failed = 0
        self.registrations = 0
        self.token_refreshes = 0
        self.logouts = 0

        # ── Per-endpoint metrics ─────────────────────────────────────────────
        self._endpoints: Dict[str, EndpointMetrics] = defaultdict(EndpointMetrics)

    # ── Generic increment ────────────────────────────────────────────────────
    def increment(self, name: str, amount: int = 1):
        with self._lock:
            if hasattr(self, name) and isinstance(getattr(self, name), int):
                setattr(self, name, getattr(self, name) + amount)

    # ── Endpoint recording ───────────────────────────────────────────────────
    def record_request(self, endpoint: str, status_code: int, duration_ms: float):
        """Record a completed API request."""
        # Normalize endpoint: strip query params, limit key length
        normalized = endpoint.split("?")[0][:100]
        self._endpoints[normalized].record_request(status_code, duration_ms)

    def record_latency(self, endpoint: str, ms: float):
        """Record latency for an endpoint without status code context."""
        normalized = endpoint.split("?")[0][:100]
        self._endpoints[normalized].latency.record(ms)

    # ── Cache helpers ────────────────────────────────────────────────────────
    def record_cache_hit(self):
        with self._lock:
            self.cache_hits += 1

    def record_cache_miss(self):
        with self._lock:
            self.cache_misses += 1

    def cache_hit_ratio(self) -> Optional[float]:
        with self._lock:
            total = self.cache_hits + self.cache_misses
            if total == 0:
                return None
            return round(self.cache_hits / total * 100, 2)

    # ── Uptime ───────────────────────────────────────────────────────────────
    def uptime_seconds(self) -> float:
        return round(time.time() - self._start_time, 1)

    # ── Summary ─────────────────────────────────────────────────────────────
    def get_metrics(self) -> dict:
        """Return all system-level metrics (legacy-compatible)."""
        with self._lock:
            return {
                "db_retries": self.db_retries,
                "timeouts": self.timeouts,
                "rate_limit_hits": self.rate_limit_hits,
                "circuit_breaker_opens": self.circuit_breaker_opens,
                "ai_failures": self.ai_failures,
                "ocr_failures": self.ocr_failures,
                "recovery_mode_activations": self.recovery_mode_activations,
            }

    def get_summary(self) -> dict:
        """Return full observability summary for the monitoring dashboard."""
        with self._lock:
            cache_total = self.cache_hits + self.cache_misses
            system = {
                "uptime_seconds": self.uptime_seconds(),
                "uptime_human": _format_uptime(self.uptime_seconds()),
                "db_retries": self.db_retries,
                "timeouts": self.timeouts,
                "rate_limit_hits": self.rate_limit_hits,
                "circuit_breaker_opens": self.circuit_breaker_opens,
                "ai_failures": self.ai_failures,
                "ocr_failures": self.ocr_failures,
                "recovery_mode_activations": self.recovery_mode_activations,
                "cache": {
                    "hits": self.cache_hits,
                    "misses": self.cache_misses,
                    "hit_ratio_pct": round(self.cache_hits / cache_total * 100, 2) if cache_total > 0 else None,
                },
                "auth": {
                    "logins_success": self.logins_success,
                    "logins_failed": self.logins_failed,
                    "registrations": self.registrations,
                    "token_refreshes": self.token_refreshes,
                    "logouts": self.logouts,
                },
                "background_jobs": {
                    "total": self.bg_jobs_total,
                    "success": self.bg_jobs_success,
                    "failed": self.bg_jobs_failed,
                },
            }

        endpoints_summary = {
            ep: data.summary()
            for ep, data in list(self._endpoints.items())
        }

        return {
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "system": system,
            "endpoints": endpoints_summary,
        }


def _format_uptime(seconds: float) -> str:
    """Human-readable uptime string."""
    s = int(seconds)
    days, s = divmod(s, 86400)
    hours, s = divmod(s, 3600)
    minutes, s = divmod(s, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{s}s")
    return " ".join(parts)


# ── Global singleton ─────────────────────────────────────────────────────────
obs_metrics = ObservabilityMetrics()
