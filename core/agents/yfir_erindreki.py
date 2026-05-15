"""
Sprint 83 — YfirErindreki (Orchestrator)
Miðlægur stjórnandi með tvær rásir: VitansErindreki (default) + HvelfingarErindreki (vault).
"""
import sys, os, time, logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from typing import Dict, List, Optional
from dataclasses import dataclass, field

from core.agent_core_v5 import Agent, AgentResult, ComplexityScore, calculate_complexity
from core.agents.hvelfingar_erindreki import HvelfingarErindreki
from core.agents.vitans_erindreki import VitansErindreki
from core.agents.pii_sentry import detect_pii, strip_pii_for_search

logger = logging.getLogger("alvitur.orchestrator")

# ── Circuit Breaker ──────────────────────────────────────

@dataclass
class CircuitBreaker:
    """Verndar gegn keðjuverkandi villum."""
    max_failures: int = 3
    reset_timeout: float = 60.0
    failure_count: int = 0
    last_failure_time: float = 0.0
    is_open: bool = False
    
    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.max_failures:
            self.is_open = True
            logger.warning(f"Circuit breaker opnaður eftir {self.failure_count} villur")
    
    def record_success(self):
        self.failure_count = 0
        self.is_open = False
    
    def can_execute(self) -> bool:
        if not self.is_open:
            return True
        if time.time() - self.last_failure_time > self.reset_timeout:
            self.is_open = False
            self.failure_count = 0
            return True
        return False

# ── Semantic Cache ───────────────────────────────────────

class SemanticCache:
    """Einfalt skyndiminni fyrir samhljóða fyrirspurnir."""
    def __init__(self, max_size: int = 100):
        self._cache: Dict[str, AgentResult] = {}
        self._max_size = max_size
    
    def get(self, query: str) -> Optional[AgentResult]:
        return self._cache.get(query.strip().lower())
    
    def set(self, query: str, result: AgentResult):
        if len(self._cache) >= self._max_size:
            self._cache.pop(next(iter(self._cache)))
        self._cache[query.strip().lower()] = result

# ── YfirErindreki ────────────────────────────────────────

class YfirErindreki:
    """
    Aðal-stjórnandi fyrir allar fyrirspurnir.
    
    Tvær rásir í V1:
    - VitansErindreki (default) fyrir almennar fyrirspurnir
    - HvelfingarErindreki fyrir vault fyrirspurnir + PII
    """
    
    def __init__(self):
        self._agents: Dict[str, Agent] = {}
        self._cache_vitinn = SemanticCache()
        self._cache_hvelfing = SemanticCache()
        self._breaker = CircuitBreaker()
        self._skra_agenta()
    
    def _skra_agenta(self):
        """Skrá alla tiltæka agenta."""
        vault = HvelfingarErindreki()
        self._agents[vault.name] = vault
        
        vitans = VitansErindreki()
        self._agents[vitans.name] = vitans
        
        logger.info(f"Agenta skráðir: {list(self._agents.keys())}")
    
    async def handle(self, query: str, tier: str = "general",
                     attached_files: list = None,
                     search_context: dict = None) -> AgentResult:
        import sys
        if search_context:
            print(f"DEBUG2 Yfir: search_context type={type(search_context).__name__}, keys={list(search_context.keys()) if hasattr(search_context, 'keys') else 'N/A'}", file=sys.stderr)
            print(f"DEBUG2 Yfir: citations={search_context.get('citations', 'KEY_MISSING')}", file=sys.stderr)
        else:
            print(f"DEBUG2 Yfir: search_context is None", file=sys.stderr)
        """Aðal-aðferðin. Tekur á móti fyrirspurn og skilar niðurstöðu."""
        start = time.time()
        
        # 1. PII Sentry
        pii_result = detect_pii(query)
        if pii_result["has_pii"]:
            logger.info(f"PII fannst: {pii_result['pii_types']}")
        
        # 2. Complexity Score
        complexity = calculate_complexity(query, tier)
        logger.info(f"Flækjustig: {complexity.score:.2f} ({complexity.reasoning})")
        
        # 3. Velja agent — byggt á tier fyrst, síðan PII
        if tier == "vault":
            agent = self._agents.get("HvelfingarErindreki")
            cache = self._cache_hvelfing
        elif pii_result["has_pii"]:
            agent = self._agents.get("HvelfingarErindreki")
            cache = self._cache_hvelfing
            logger.info(f"PII beinir í Hvelfingu: {pii_result['pii_types']}")
        else:
            agent = self._agents.get("VitansErindreki")
            cache = self._cache_vitinn
        
        if not agent:
            return AgentResult(
                response="Enginn agent tiltækur fyrir þessa fyrirspurn.",
                confidence=0.0, agent_name="orchestrator", tier=tier
            )
        
        # 4. Skyndiminni — nota rétta cache-ið
        cached = cache.get(query)
        if cached:
            logger.info(f"Skyndiminnishitt ({agent.name})")
            return cached
        
        # 5. Circuit Breaker
        if not self._breaker.can_execute():
            return AgentResult(
                response="Þjónusta tímabundið óvirk vegna tæknivanda.",
                confidence=0.0, agent_name="orchestrator", tier=tier
            )
        
        # 6. Undirbúa context
        context = {
            "tier": tier,
            "pii_detected": pii_result["has_pii"],
            "pii_warning": pii_result["warning"],
            "complexity": complexity,
            "search_text": search_context.get("search_text", "") if search_context else "",
            "citations": search_context.get("citations", []) if search_context else [],
            "file_context": search_context.get("file_context", "") if search_context else "",
        }
        
        # 7. Framkvæma
        try:
            result = await agent.execute(query, context)
            self._breaker.record_success()
            cache.set(query, result)
            return result
        except Exception as e:
            logger.error(f"Agent villa: {e}")
            self._breaker.record_failure()
            return AgentResult(
                response="Villa kom upp við úrvinnslu fyrirspurnar.",
                confidence=0.0, agent_name=agent.name, tier=tier
            )

# Singleton
yfir_erindreki = YfirErindreki()
