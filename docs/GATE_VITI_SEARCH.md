# GATE_VITI_SEARCH.md — Provider-val fyrir Vitann (ytri leit)

**Ákvörðun tekin:** 7. júní 2026
**Af:** Opus 4.8 (yfirstrategisti)
**Staða:** 🟢 GREEN — háð tveimur tæknilegum hliðum

---

## 1. Provider-val

| Hlutverk | Provider | Lögsaga | Index | Athugasemd |
|----------|----------|---------|-------|------------|
| **Aðal** | **Staan** (Qwant/Ecosia) | 🇫🇷🇩🇪 EU (París) | Sjálfstætt evrópskt | EU-sovereign, núll-tracking sjálfgefið |
| **Backup** | **Mojeek** | 🇬🇧 UK (post-Brexit) | Sjálfstætt | GDPR-adequate en utan EES → aukahlutverk |

**Rökstuðningur:** Bæði eru sjálfstæð index (ekki Bing/Google), hönnuð fyrir AI-chatbot og deep-research. Staan er EU-sovereign og hefur forgang sem almenn-vef provider — íslenskar fullvalda heimildir (Alþingi, Hagstofa o.fl.) raðast áfram fyrst fyrir íslenskar fyrirspurnir, samkvæmt tier-kerfi Sprint 87. Mojeek veitir lögsögu-fjölbreytni og þekju-uppfylling.

**Athugið:** Staan er ungt index (ágúst 2025, FR/DE fyrst). Íslensk efnis-þekja er **ósannreynd** — prófa skal með íslenskum lögfræði-fyrirspurnum um leið og API-lykill berst (mánudagur).

---

## 2. Tvö tæknileg hlið (ÞVINGUÐ)

### Hlið 1: Sótthreinsunarlag fyrir útleið
- **Krafa:** ENGIN PII / vault-gögn / viðkvæmt samhengi mega fara út í leitar-fyrirspurn.
- **Útfærsla:** Sótthreinsunarlag (sanitization) áður en fyrirspurn fer á Staan/Mojeek. Sami harði múr og á Stórmeistaranum.
- **Áhætta:** Í agentic flæði getur Erindrekinn óvart smíðað fyrirspurn úr viðkvæmu inntaki.

### Hlið 2: Innleiðingar-gate (tvennt)
- **(a) Gæði:** Lögfræðileg nákvæmni — tengist V1-RAG-001.
- **(b) Prompt-injection vörn:** Vefefni sem fer inn í agent er injection-vektor. Sía skal vefniðurstöður áður en þær fara í prompt.
- **(c) Provenance:** Ytri vefniðurstöður verða **merktar sem vefur/ytri**, aðgreindar frá fullvalda Lagasafns-tilvitnunum. Vefefni má aldrei dulbúast sem staðfest lög.

---

## 3. Arkitektúr — skýr aðgreining

| Lag | Lýsing | Ytri leit? |
|-----|--------|------------|
| **Hvelfingin (vault)** | Læst, fullvalda, gögn fara ALDREI út | ❌ Nei |
| **Vitinn / Erindrekinn** | Opinber þekkingar-öflun | ✅ Já, í gegnum gate |
| **Lagasafn (Qdrant)** | Fullvalda íslensk lög | ❌ Nei |

---

## 4. Scope / tímasetning

Ytri leit er **EKKI launch-critical.** Beta keyrir á Lagasafns-RAG-inu (Qdrant) án vefleitar. Staan er gæða-viðbót, gengur í parallel/eftir.

---

## 5. Skyld skjöl

- `V1-RAG-001` — gæðamæling fyrir retrieval
- `ADR-006` — arkitektúr-ákvörðun
- `SPRINT80C_WEBSEARCH_DISCOVERY.md` — fyrri websearch rannsókn
- `RISK_REGISTER.md` — áhættuskráning

---

## 6. Saga — Mojeek/ytri leit í eldri skjölum

| Skjal | Lykilatriði | Samræmi við GATE? |
|-------|-------------|-------------------|
| SPRINT80C_WEBSEARCH_DISCOVERY.md | Mojeek API rannsakað (virkur lykill, £10 inneign, XML/JSON) | ✅ Passar |
| SPRINT87_STRATEGY.md | Mojeek skilgreint sem tier 3, sovereign=false, vault-bypass | ✅ Fullkomið samræmi |
| SPRINT88_DISCOVERY.md | Per-source latency, en Staan ekki nefnt | 🔶 Staan er nýtt |
| ADR-006.md | Vatnsmerki — Vitinn ON, Hvelfing OFF | 🔷 Ótengt beint |

**Niðurstaða:** Nýja GATE_VITI_SEARCH.md er í fullu samræmi við eldri ákvarðanir. Staan er viðbót (nýr aðal-provider) en breytir ekki arkitektúrnum.
