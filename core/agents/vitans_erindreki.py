"""
Sprint 90 — VitansErindreki (SearchAgent with Context Sanitization)
Almennur leitaragent fyrir Vitann. Notar vLLM með ytri heimildum.
Tier = "vitinn", requires_external = True.
Enforces Lesson #112: Server-side Context Sanitization & Audit Extraction.
"""
import sys, os, time, re
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
        return 0.001  # Staðbundið vLLM, nánast enginn kostnaður
    
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
        
                    f"Þú ert Alvitur — íslenskur sérfræðingur.\n\n"
            f"=== ÍSLENSK ALÞEKKING (grunnur) ===\n"
            f"KENNITÖLUR: Íslensk kennitala er 10 stafa: DDMMÁÁ-RRVÖ. Fyrstu 6 = fæðingardagur. "
            f"Stafur 7-8 = raðnúmer. Stafur 9 = vartala (Mod-11 með vægjum 3,2,7,6,5,4,3,2). "
            f"Stafur 10 = aldarstafur (8=1800, 9=1900, 0=2000). "
            f"+40 reglan: Fyrirtækja-kt byrja á 41-71 (dagsetningu +40). Einstaklings-kt byrja á 01-31. "
            f"BANKAREIKNINGAR: 12 stafa: BBBB-HH-RRRRRR. Fyrstu 4 = banki+útibú (01=Landsbanki, 03=Íslandsbanki, 05=Arion). "
            f"Næstu 2 = höfuðbók (26=veltureikningur, 05/14/15=sparireikningur). Síðustu 6 = raðnúmer.\n"
            f"FÉLAGAFORM: ehf. (einkahlutafélag, lágmark 500.000 kr), hf. (hlutafélag, 4 millj.), "
            f"ohf. (opinbert hf.), sf. (sameignarfélag, ótakmörkuð ábyrgð), slf. (samlagsfélag), "
            f"slhf. (samlagshlutafélag), ses. (sjálfseignarstofnun), svf. (samvinnufélag), bs. (byggðasamlag).\n"
            f"Fyrirtækjanöfn með þessum endingu eru lögaðilar, EKKI einstaklingar — þau teljast ekki til PII.\n\n"
            f"=== HEIMILDIR (RAUNTÍMAGÖGN) ===\n{search_text}{file_context}\n\n"
            f"REGLUR:\n"
            f"1. Heimildir þessar hafa forgang.\n"
            f"2. Þú VERÐUR að byggja svarið á heimildum sem eru í context.\n"
            f"3. Ef Hagstofa-heimild er í context og á við spurninguna, ÞÁ VERÐUR þú að vísa í hana og nota hana sem aðalheimild.\n"
            f"4. ALDREI skálda, búa til eða nefna heimildir sem eru ekki í context. Ekki nefna uppspunnar heimildir eins og 'Íslandsbanki', 'Statistíðnaði' eða annað sem er ekki raunverulega í heimildalistanum.\n"
            f"5. Ef engin viðeigandi heimild er í context, segðu það beint og skýrt.\n"
            f"6. Ekki fullyrða meira en heimildirnar styðja.\n"
            f"7. Svaraðu á íslensku.\n\n"
            f"SPURNING: {query}"

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
                raw_content = data["choices"][0]["message"]["content"].strip()
                model = VAULT_LOCAL_MODEL.rsplit("/", 1)[-1]
                
                # Áfangi 0 (Lesson #112): Draga út innri rökfærslu / áform fyrir audit logga
                think_match = re.search(r"<think>(.*?)</think>", raw_content, flags=re.DOTALL)
                extracted_thinking = think_match.group(1).strip() if think_match else ""
                
                # Samhengis-hreinsun: Strippa <think> alveg út áður en Guard eða minni fá skjalið
                clean_content = re.sub(r"<think>.*?</think>", "", raw_content, flags=re.DOTALL).strip()
                
                # Skilum hreinu svari en geymum rökfærsluna í metadata fylki fyrir Áfanga 2
                result = AgentResult(
                    response=clean_content, citations=citations,
                    confidence=0.85, cost_usd=self.cost_per_call,
                    agent_name=self.name, model_used=model, tier="vitinn"
                )
                
                # Geymum tímabundið á formi sem audit logginn (Áfangi 2) mun lesa beint
                result.metadata = {"actions_logged": extracted_thinking}
                
                self.log_result(result, (time.time() - start) * 1000)
                return result
                
        except Exception as e:
            import sys
            print(f"VitansErindreki villa: {e}", file=sys.stderr)
            return AgentResult(
                response="Villa kom upp við leit.", confidence=0.0,
                cost_usd=0.0, agent_name=self.name, tier="vitinn"
            )
