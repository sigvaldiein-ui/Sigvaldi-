"""
Sprint 83 — Öryggisþættir: Context Pruning + Semantic Cache + Circuit Breaker
Innleidd samkvæmt hönnun Aðals.
"""
import time, hashlib, logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger("alvitur.security")

# ── Context Pruning ─────────────────────────────────────

def prune_context(
    search_text: str,
    citations: List[Dict],
    max_chars: int = 4000,
    keep_first_n: int = 3
) -> Tuple[str, List[Dict]]:
    """
    Stytta samhengi til að spara orku og bæta nákvæmni.
    
    Reglur:
    1. Halda fyrstu N citations alltaf
    2. Ef texti er of langur, stysta hann
    3. Skila alltaf eitthvað
    """
    if not search_text and not citations:
        return "", []
    
    # Takmarka fjölda citations
    pruned_citations = citations[:keep_first_n] if len(citations) > keep_first_n else citations
    
    # Stytta texta ef þörf
    if len(search_text) > max_chars:
        # Halda byrjun og enda
        half = max_chars // 2
        search_text = search_text[:half] + "\n...\n" + search_text[-half:]
    
    return search_text, pruned_citations


# ── Semantic Cache ──────────────────────────────────────

@dataclass
class CacheEntry:
    result: dict
    timestamp: float = field(default_factory=time.time)
    hits: int = 0

class SemanticCache:
    """
    Skyndiminni sem endurnýtir svör fyrir samhljóða fyrirspurnir.
    Notar einfaldan strengjasamanburð í V1.
    """
    def __init__(self, max_size: int = 100, ttl_seconds: float = 3600):
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._ttl = ttl_seconds
    
    def _normalize(self, query: str) -> str:
        """Staðla fyrirspurn fyrir samanburð."""
        q = query.strip().lower()
        # Fjarlægja greinarmerki
        import re
        q = re.sub(r'[?!.,;:"]', '', q)
        return q
    
    def get(self, query: str) -> Optional[dict]:
        """Sækja úr skyndiminni."""
        key = self._normalize(query)
        entry = self._cache.get(key)
        if entry:
            if time.time() - entry.timestamp < self._ttl:
                entry.hits += 1
                logger.info(f"Skyndiminnishitt: {key[:50]} (hits={entry.hits})")
                return entry.result
            else:
                del self._cache[key]
        return None
    
    def set(self, query: str, result: dict):
        """Vista í skyndiminni."""
        if len(self._cache) >= self._max_size:
            # Fjarlægja elsta færslu
            oldest_key = min(self._cache, key=lambda k: self._cache[k].timestamp)
            del self._cache[oldest_key]
        
        key = self._normalize(query)
        self._cache[key] = CacheEntry(result=result)
        logger.info(f"Skyndiminni vistað: {key[:50]}")
    
    def stats(self) -> dict:
        """Skila tölfræði um skyndiminni."""
        total_hits = sum(e.hits for e in self._cache.values())
        return {
            "entries": len(self._cache),
            "max_size": self._max_size,
            "total_hits": total_hits,
            "ttl_seconds": self._ttl
        }


# ── Circuit Breaker ────────────────────────────────────

class CircuitBreaker:
    """
    Verndar gegn keðjuverkandi villum.
    Ef of margar villur koma í röð, opnast rásin tímabundið.
    """
    def __init__(self, max_failures: int = 3, reset_timeout: float = 60.0):
        self.max_failures = max_failures
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.is_open = False
        self.total_failures = 0
        self.total_successes = 0
    
    def record_failure(self):
        """Skrá villu."""
        self.failure_count += 1
        self.total_failures += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.max_failures:
            self.is_open = True
            logger.warning(f"Circuit breaker opnaður ({self.failure_count} villur)")
    
    def record_success(self):
        """Skrá árangur."""
        if self.failure_count > 0:
            self.failure_count = 0
            self.is_open = False
            logger.info("Circuit breaker endurstilltur")
        self.total_successes += 1
    
    def can_execute(self) -> bool:
        """Athuga hvort hægt sé að framkvæma."""
        if not self.is_open:
            return True
        if time.time() - self.last_failure_time > self.reset_timeout:
            # Half-open: leyfa eina tilraun
            self.is_open = False
            self.failure_count = 0
            logger.info("Circuit breaker half-open — leyfi eina tilraun")
            return True
        return False
    
    def stats(self) -> dict:
        """Skila tölfræði."""
        return {
            "is_open": self.is_open,
            "failure_count": self.failure_count,
            "total_failures": self.total_failures,
            "total_successes": self.total_successes
        }
