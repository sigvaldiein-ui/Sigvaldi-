# 🏛️ ADR-008: CAPABILITY REGISTRY & TIER ENFORCEMENT

**Staða:** Innleitt og sannprófað (Sprettir 99 & 97.6)
**Markmið:** Að skilgreina aðgangsstýringu að verkfærum og aðskilja uppflettingu frá heimildavottun.

* **Samhengi:** Eldri útfærsla blandaði saman því að sækja verkfæri og staðfesta aðgang, sem leiddi til sjálfheldu þegar `user_tier` féll niður í "Vitinn" sem sjálfgefið gildi. 
* **Ákvörðun:** 1. Aðskilja rökfræði: `get_tool(name)` er nú hrein, hlutlaus uppfletting. `check_tier_for_tool(tool_name, user_tier)` er sjálfstætt öryggismillilag keyrt við API landamærin.
    2. Skilgreina `CRITICAL_TOOLS = {"mail_send", "api_exec", "pdf_gen"}` til að flagga tól sem krefjast undantekningarlaust mannlegrar samþykktar (HITL).
* **Afleiðing:** Verkfæraköll eru nú algjörlega varin gegn "Tier Bypass". Engin aðgerð fer í gegn án þess að JW-Token staðfesti réttindi notandans.
