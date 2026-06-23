"""Sprint 89 – In-memory vöktun fyrir hraða, skyndiminnishitt og villur."""
import time
import threading
from collections import deque


class Monitor:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._cache_hits = 0
        self._cache_misses = 0
        self._errors = 0
        self._latencies = deque(maxlen=200)
        self._start_time = time.time()

    def record_cache_hit(self):
        self._cache_hits += 1

    def record_cache_miss(self):
        self._cache_misses += 1

    def record_latency(self, ms: float):
        self._latencies.append(ms)

    def record_error(self):
        self._errors += 1

    @property
    def cache_hit_rate(self) -> float:
        total = self._cache_hits + self._cache_misses
        if total == 0:
            return 0.0
        return self._cache_hits / total

    @property
    def avg_latency_ms(self) -> float:
        if not self._latencies:
            return 0.0
        return sum(self._latencies) / len(self._latencies)

    @property
    def uptime_seconds(self) -> float:
        return time.time() - self._start_time

    def stats(self) -> dict:
        return {
            "cache_hit_rate": round(self.cache_hit_rate, 4),
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "errors": self._errors,
            "uptime_seconds": round(self.uptime_seconds, 2)
        }


_monitor = Monitor()


def get_monitor():
    return _monitor
