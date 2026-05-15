"""
Sprint 83 — VitansErindreki (SearchAgent)
Almennur leitaragent fyrir Vitann. Notar vLLM með ytri heimildum.
Tier = "vitinn", requires_external = True.
"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.agent_core_v5 import Agent, AgentResult, ComplexityScore
from typing import Dict
import httpx

class VitansErindreki(Agent):
    """SearchAgent — almennar fyrirspurnir með aðgang að ytri heimildum."""
    
    @property
    def name(self) -> str:
        return "VitansErindreki"
    
    @property
    def cost_per_call(self) -> float:
        return 0.001  # Staðbundið vLLM, nánast ekkert kostnaður
    
    @property
    def tier(self) -> str:
        return "vitinn"
    
    async def can_handle(self, query: str, complexity: ComplexityScore) -> float:
        """Getur svarað öllum almennum fyrirspurnum."""
        if complexity.requires_external:
            return 0.9
        return 0.85
    
    async def execute(self, query: str, context: dict) -> AgentResult:
        """Framkvæmir almenna fyrirspurn með vLLM + ytri heimildum."""
        from interfaces.config import VAULT_LOCAL_URL, VAULT_LOCAL_MODEL, VAULT_LOCAL_TIMEOUT
        
        start = time.time()
        search_text = context.get("search_text", "")
        citations = context.get("citations", [])
        file_context = context.get("file_context", "")
        
        system_prompt = (
            f"Þú ert Alvitur — íslenskur sérfræðingur.\n\n"
            f"=== HEIMILDIR (RAUNTÍMAGÖGN) ===\n{search_text}{file_context}\n\n"
            f"REGLUR:\n"
            f"1. Heimildir hafa forgang.\n"
            f"2. Ef heimildir vantar, segðu það hreint út.\n"
            f"3. Svaraðu á íslensku.\n\n"
            f"SPURNING: {query}"
        )
        
        try:
            async with httpx.AsyncClient(timeout=float(VAULT_LOCAL_TIMEOUT)) as client:
                resp = await client.post(
                    VAULT_LOCAL_URL,
                    json={
                        "model": VAULT_LOCAL_MODEL,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": query}
                        ],
                        "max_tokens": 4096,
                        "temperature": 0.3
                    }
                )
                if resp.status_code != 200:
                    return AgentResult(
                        response="Leitarþjónusta tímabundið ekki tiltæk.",
                        confidence=0.0, cost_usd=0.0,
                        agent_name=self.name, tier="vitinn"
                    )
                
                data = resp.json()
                content = data["choices"][0]["message"]["content"].strip()
                model = VAULT_LOCAL_MODEL.rsplit("/", 1)[-1]
                
                result = AgentResult(
                    response=content, citations=citations,
                    confidence=0.85, cost_usd=self.cost_per_call,
                    agent_name=self.name, model_used=model, tier="vitinn"
                )
                
                self.log_result(result, (time.time() - start) * 1000)
                return result
                
        except Exception as e:
            import sys
            print(f"VitansErindreki villa: {e}", file=sys.stderr)
            return AgentResult(
                response="Villa kom upp við leit.", confidence=0.0,
                cost_usd=0.0, agent_name=self.name, tier="vitinn"
            )
