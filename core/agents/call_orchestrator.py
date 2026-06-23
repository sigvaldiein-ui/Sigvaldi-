"""
Miðlægt kall á YfirErindreka — eitt fall, allir staðir.
"""
import logging, time
from core.agents.yfir_erindreki import yfir_erindreki
from core.monitor import get_monitor

logger = logging.getLogger("alvitur.orchestrator")

async def call_orchestrator(query: str, tier: str, attachments: list, search_text: str,
                            citations: list, file_context: str = "", domain: str = "legal"):
    """
    Miðlægt kall á YfirErindreka.
    Setur saman orchestrator_context og kallar á yfir_erindreki.handle().
    Skilar AgentResult hlutnum beint.
    """
    orchestrator_context = {
        "search_text": search_text,
        "citations": citations,
        "file_context": file_context,
        "domain": domain,
    }
    start = time.time()
    result = await yfir_erindreki.handle(query, tier, attachments, orchestrator_context)
    elapsed = (time.time() - start) * 1000
    monitor = get_monitor(); monitor.record_latency(elapsed)
    logger.debug(f"[Orchestrator] {result.agent_name} | {elapsed:.0f}ms | confidence={result.confidence}")
    return result
