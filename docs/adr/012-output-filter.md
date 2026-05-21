# 🏛️ ADR-012: PRO-MODE OUTPUT FILTER & CIRCUIT BREAKER

**Staða:** Innleitt og sannprófað (Sprettir 101 & 106)
**Markmið:** Að tryggja einangrun gagna og koma í veg fyrir "Schema Drift" hrönn.

* **Samhengi:** API-köll í ytri gagnagrunna geta skilað ófyrirsjáanlegum eða breyttum gögnum. LLM líkön eiga það til að ofskynja (hallucinate) ef þau fá tóm eða gæðalítil fylki.
* **Ákvörðun:**
    1. Ströng "Whitelist" sía (Pro-Mode) hreinsar öll svör áður en þau ná í LLM kjarnann.
    2. Ef sían strípar út öll gögn vegna þess að ytra schema hefur breyst, er hringrásin rofin (Fail-Closed).
    3. Atvikið er loggað dulkóðað sem `CRITICAL_SCHEMA_DRIFT` og LLM líkaninu er skilað staðlaðri villu, sem kemur í veg fyrir gagnaleka og stjórnleysi.
* **Afleiðing:** Kerfið deyr ekki þótt umhverfið breytist, heldur grípur villuna á öruggan, fyrirsjáanlegan hátt.
