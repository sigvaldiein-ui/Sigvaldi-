"""
Sprint 83 — Agent Core v5
Multi-agent foundation: abstract interface, cost tracking, tier awareness.
Byggt á Aðal's hönnun og Opus verkbeiðni.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import time, logging

logger = logging.getLogger("alvitur.agent")

# ── Gagnaskipanir ──────────────────────────────────────────────

@dataclass
class AgentResult:
    """Niðurstaða frá agent."""
    response: str
    citations: List[Dict] = field(default_factory=list)
    confidence: float = 0.0
    cost_usd: float = 0.0
    agent_name: str = ""
    model_used: str = ""
    tier: str = "general"
    metadata: Dict = field(default_factory=dict)

@dataclass
class ComplexityScore:
    """Flækjustig fyrirspurnar."""
    score: float = 0.0            # 0.0–1.0
    domain: str = "general"       # general / legal / vault
    requires_external: bool = False
    estimated_tokens: int = 0
    reasoning: str = ""

# ── Abstract Agent Interface ────────────────────────────────────

class Agent(ABC):
    """Grunnur fyrir alla sérhæfða agenta."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Heiti agents."""
        ...
    
    @property
    @abstractmethod
    def cost_per_call(self) -> float:
        """Áætlaður kostnaður í USD á hvert kall."""
        ...
    
    @property
    @abstractmethod
    def tier(self) -> str:
        """Tier sem agent tillheyrir (vault / legal / general)."""
        ...
    
    @abstractmethod
    async def can_handle(self, query: str, complexity: ComplexityScore) -> float:
        """Skilar confidence 0-1 að agent geti svarað."""
        ...
    
    @abstractmethod
    async def execute(self, query: str, context: dict) -> AgentResult:
        """Framkvæmir fyrirspurn og skilar niðurstöðu."""
        ...
    
    def log_result(self, result: AgentResult, elapsed_ms: float):
        """Skráir niðurstöðu í audit trail."""
        logger.info(
            f"[AGENT] {self.name} | confidence={result.confidence:.2f} "
            f"cost=${result.cost_usd:.4f} | time={elapsed_ms:.0f}ms | "
            f"tier={result.tier} | model={result.model_used}"
        )

# ── Complexity Calculator ──────────────────────────────────────

def calculate_complexity(query: str, domain: str = "general") -> ComplexityScore:
    """
    Reiknar flækjustig fyrirspurnar.
    Aðal's formúla: lengd × domain þyngd × leitarorðafjöldi.
    """
    words = len(query.split())
    keywords = sum(1 for kw in ["lög", "lag", "réttur", "persónuvernd", "samning", 
                                "dómur", "ákvæði", "reglugerð", "grein", "málsgrein"] 
                   if kw in query.lower())
    
    # Grunnstig eftir lengd
    if words < 5:
        base = 0.2
    elif words < 15:
        base = 0.4
    elif words < 30:
        base = 0.6
    else:
        base = 0.8
    
    # Domain þyngd
    domain_mult = {"legal": 1.5, "general": 1.0, "vault": 0.8}
    
    # Flækjustig = grunnur + leitarorð + domain
    score = min(1.0, base + (keywords * 0.1) * domain_mult.get(domain, 1.0))
    
    return ComplexityScore(
        score=score,
        domain=domain,
        requires_external=(domain != "vault"),
        estimated_tokens=words * 3,
        reasoning=f"words={words}, keywords={keywords}, domain={domain}"
    )
