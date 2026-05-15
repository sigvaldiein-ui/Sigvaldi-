"""
Sprint 83 — HvelfingarErindreki (VaultAgent)
Sérhæfður agent fyrir trúnaðarfyrirspurnir. Notar aðeins staðbundið vLLM.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.agent_core_v5 import Agent, AgentResult, ComplexityScore
from typing import Dict

class HvelfingarErindreki(Agent):
    """Trúnaðaragent — sovereign only, ekkert ytra API."""
    
    @property
    def name(self) -> str:
        return "HvelfingarErindreki"
    
    @property
    def cost_per_call(self) -> float:
        return 0.001
    
    @property
    def tier(self) -> str:
        return "vault"
    
    async def can_handle(self, query: str, complexity: ComplexityScore) -> float:
        if complexity.domain == "vault":
            return 0.95
        if complexity.requires_external:
            return 0.3
        return 0.7
    
    async def execute(self, query: str, context: dict) -> AgentResult:
        """Framkvæmir trúnaðarfyrirspurn með staðbundnu vLLM."""
        from interfaces.config import VAULT_LOCAL_URL, VAULT_LOCAL_MODEL, VAULT_LOCAL_TIMEOUT
        import httpx, time
        
        start = time.time()
        
        # Sækja leitarsamhengi (PII-hreinsað)
        search_text = context.get("search_text", "")
        citations = context.get("citations", []) if context.get("citations") else []
        file_context = context.get("file_context", "")
        
        # DEBUG: sjá hvað við fengum
        print(f"DEBUG Hvelfing: search_text={len(search_text)} stafir, citations={len(citations)}", file=sys.stderr)
        
        system_prompt = (
            f"Thu ert Alvitur — íslenskur trúnaðar-agentur.\n\n"
            f"HEIMILD-GOGN:\n{search_text}{file_context}\n\n"
            f"REGLUR: 1. Heimildir hafa algjöran forgang. "
            f"2. Ef heimildir vantar, segðu það hreint út. "
            f"3. Stutt, nákvæmt svar.\n\n"
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
                        response="Trúnaðarþjónusta tímabundið ekki tiltæk.",
                        confidence=0.0,
                        cost_usd=0.0,
                        agent_name=self.name,
                        tier="vault"
                    )
                
                data = resp.json()
                content = data["choices"][0]["message"]["content"].strip()
                model = VAULT_LOCAL_MODEL.rsplit("/", 1)[-1]
                
                result = AgentResult(
                    response=content,
                    citations=citations,
                    confidence=0.9,
                    cost_usd=self.cost_per_call,
                    agent_name=self.name,
                    model_used=model,
                    tier="vault"
                )
                
                self.log_result(result, (time.time() - start) * 1000)
                return result
                
        except Exception as e:
            import traceback
            print(f"HvelfingarErindreki villa: type={type(e).__name__} msg='{str(e)}'", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            return AgentResult(
                response="Villa kom upp í trúnaðarþjónustu.",
                confidence=0.0,
                cost_usd=0.0,
                agent_name=self.name,
                tier="vault"
            )
