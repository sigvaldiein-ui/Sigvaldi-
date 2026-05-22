# 🏛️ ADR-009: AGENTIC SANDBOX & TÆKJAEINANGRUN (API_EXEC)

**Staða:** Samþykkt og innleitt (Backfilled fyrir Sprett 100.x)
**Ábyrgðamaður:** Aðal (Yfirarkítekt)

## 1. Samhengi og Rökstuðningur
Til að "Starfsmaðurinn" (Digital Worker) geti leyst flókin stjórnsýsluverkefni þarf hann aðgengi að ytri gögnum í gegnum `Api_execTool`. Ef þetta tól er skilið eftir opið, skapast hins vegar gríðarleg hætta á Server-Side Request Forgery (SSRF) og gagna-leka, þar sem LLM-líkanið gæti verið blekkt (Prompt Injection) til að senda viðkvæm gögn á óviðkomandi netþjóna.

## 2. Ákvörðun
Við innleiðum tvöfalda sandkassa-vörn (Sandbox) á netlaginu fyrir öll útleiðandi API köll:

1.  **Harðkóðaður Whitelist-vörður (`ALLOWED_DOMAINS`):** Tólið fær aðeins að eiga samskipti við fyrirfram skilgreindan lista yfir lén íslenskrar stjórnsýslu (t.d. `api.skra.is`, `island.is`, `api.logbirting.is`).
2.  **Fail-Closed Villumeðhöndlun:** Áður en HTTP beiðni (e. request) er útbúin, er lénið greint. Ef það er ekki á `ALLOWED_DOMAINS` listanum, deyr aðgerðin samstundis og kastar `FastAPI HTTPException (403 Forbidden)`. 

## 3. Afleiðingar
* **Öryggi:** Kerfið "deyr frekar en að leka". LLM líkanið fær enga möguleika á að opna nettengingar við óþekkt lén, sem útilokar gagnaútflutning til illgjarnra aðila.
* **Takmörkun:** Ef bæta þarf við nýrri ríkisstofnun krefst það endurskrifta á kóða og nýrrar útgáfu (Deployment). Þetta er ásættanleg málamiðlun fyrir hámarksöryggi.
