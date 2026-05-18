# SPRINT87_DISCOVERY.md
**Dagsetning:** 17. maí 2026 — Sprint 87 Phase A Discovery

---

## Phase 0.1 — Live Verify ✅

| Source | HTTP | Staða | Athugasemd |
|--------|------|-------|------------|
| Alþingi XML API | 200 | ✅ | XML þingmannalisti virkt |
| Vísindavefur leit | 301→200 | ✅ | 4 svör um "hantaveira" staðfest |

---

## Phase A.1 — Hagstofa PX-Web ✅

| Atriði | Staða |
|--------|-------|
| hagstofan wrapper (pip) | ✅ v0.1.1 |
| Databases | ✅ 6 total (Atvinnuvegir, Efnahagur, Ibuar, Samfelag, Sogulegar, Umhverfi) |
| Table inventory | ~1,706 töflur |
| Data freshness | ✅ Apríl 2026 (verðbólga), Q1 2026 (atvinnuleysi, mannfjöldi) |

### Prófaðar töflur
| ID | Titill | Nýjustu gögn |
|----|--------|-------------|
| VIS01000 | Vísitala neysluverðs | Apríl 2026 |
| VIN00910 | Atvinnuleysi | Q1 2026 |
| MAN10001 | Mannfjöldi eftir sveitarfélögum | Q1 2026 |

---

## Phase A.2 — Dómstólar (uppfært)

| Atriði | Niðurstaða |
|--------|------------|
| Vefsíða | island.is/s/domstolar (flutt 6. maí 2026) |
| Dómasafn | ✅ island.is/domar — leitarviðmót til staðar |
| Dagskrá | ✅ island.is/dagskra-domstola |
| RSS | ❓ Óstaðfest |

---

## Phase A.2 — Eftir (Pending)

| Source | Staða |
|--------|-------|
| Hæstiréttur reachability | ❌ Pending |
| Persónuvernd ákvarðanir | ❌ Pending |
| Seðlabanki NSDP | ❌ Pending |
| robots.txt + ToS — allar | ❌ Pending |

---

## Source Reachability Matrix

| Source | URL | Staða | Gagnagerð |
|--------|-----|-------|-----------|
| Alþingi | althingi.is/altext/xml/ | ✅ | XML API |
| Vísindavefur | visindavefur.is/search.php | ✅ | HTML scrape |
| Hagstofa | px.hagstofa.is (hagstofan) | ✅ | Python API |
| Dómstólar | island.is/domar | 🟡 | HTML leit |
| Hæstiréttur | ? | ❌ | ? |
| Persónuvernd | ? | ❌ | ? |
| Seðlabanki NSDP | ? | ❌ | ? |

---

## Arkitektúrspurning — Phase B territory

Option A — Dynamic-only: query → heuristic map → fetch → return
Option B — Qdrant-only: query → embed → Qdrant metadata → cached snapshot
Option C — Hybrid (Opus proposal): Qdrant table discovery + dynamic API fetch alltaf

ATHUGASEMD: Phase B spurning — krefst Aðal review + Opus GREEN

---

## ToS Risk Register

| Source | Risk |
|--------|------|
| Hagstofa | 🟢 CC BY 4.0 |
| Alþingi | 🟢 Opinbert XML API |
| Vísindavefur | 🟡 robots.txt óstaðfest |
| Dómstólar | 🟡 robots.txt óstaðfest |

---

## Næstu skref
1. Klára Phase A.2 — Hæstiréttur, Persónuvernd, Seðlabanki
2. robots.txt check á öllum sources
3. Skrifa Phase B strategy doc
4. Ping Opus → Phase A GREEN → Phase B → Aðal review

---

## Phase A.2 — LOKIÐ (17. maí 2026)

| Source | URL | Staða | Gagnagerð |
|--------|-----|-------|-----------|
| Hæstiréttur | island.is/s/haestirettur | ✅ 200 | island.is CMS |
| Persónuvernd | island.is/s/personuvernd | ✅ 200 | RSS feeds + island.is CMS |
| Dómstólar | island.is/s/domstolar + /domar | ✅ 200 | island.is CMS |
| Seðlabanki API | api.sedlabanki.is | ❌ 403 | Forbidden — skip |

## Lykiluppgötvun
Hæstiréttur + Persónuvernd + Dómstólar eru öll á island.is CMS.
Persónuvernd RSS: rss.xml?organization=personuvernd (fréttir)
Persónuvernd RSS: rss.xml?genericListId=18Qfx6... (úrskurðir)

## robots.txt
althingi.is: 200, visindavefur.is: 200, hagstofa.is: 200
haestirettur.is: 301→island.is, personuvernd.is: 301→island.is, sedlabanki.is: 301

## Phase A — STATUS: ✅ LOKIÐ — Tilbúið fyrir Opus review

---

## Gap 2 — Vísindavefur clarification ✅

Niðurstaða: „4 svör" komu úr **(b) HTML leit** á visindavefur.is/search.php
- Þetta er NÝ capability — ekki gamla RSS source.py frá Sprint 86
- Vísindavefur er promotable til **Tier 2 (agentic search)** í Sprint 87
- Alvitur live test staðfesti: engar Vísindavefur citations í dag → routing vandamál

## Gap 2b — Alvitur live test findings ✅

| Spurning | Væntanlegt | Raunverulegt | Vandamál |
|----------|------------|--------------|----------|
| Hantaveira | Vísindavefur 4 svör | Almenn vélaþýðing | Routing + no integration |
| Mannfjöldi Íslands | Hagstofa Q1 2026: 383k+ | 376.000 (2021) | Hagstofa ekki tengd |
| `<think>` tags | Aldrei sjáanlegt | Lekur í svar | P0 patch þarf |

## Gap 3 — Phase B-G ordering með tímaestímötum ✅

| Phase | Verk | Tími |
|-------|------|------|
| B | Strategy doc + Aðal review | ½ dagur |
| C | 🅿️ DEFERRED → Sprint 89 (island.is CMS) | — |
| D | Hagstofa PX-Web integration | 1-1.5 dagur |
| D+1 | `<think>` tag P0 patch (Lesson #106) | 2-4 klst |
| E | Routing redesign Lesson #104 | 1 dagur |
| F | Eval regression + sovereignty_share baseline | ½ dagur |
| G | Tag v87-routing-rc1 | ½ dagur |
| **Heild** | | **3-4 dagar** |

## Gap 4 — ToS Risk Register ✅

| Source | robots.txt | Risk | Aðgerð |
|--------|-----------|------|--------|
| Hagstofa | ✅ 200 — opið | 🟢 CC BY 4.0 | Caching + attribution |
| Vísindavefur | ✅ 200 — skoða | 🟡 Óstaðfest | Rate limit + attribution |
| Alþingi | ✅ 200 — opið | 🟢 Opinbert API | Ekkert sérstaklega |
| island.is (CMS) | 301 — Sprint 89 | 🅿️ Frestað | Outreach í Sprint 89 |
| Seðlabanki | 403 Forbidden | ❌ Skip | Hagstofa dekkar gap |

Caching policy (öll sources): max 24h cache, accessed_at í citation, rate limit 1 req/s.

## Phase 0 Status ✅

| Verk | Staða | Athugasemd |
|------|-------|------------|
| 0.1 Live citations Alþingi + Vísindavefur | ✅ Lokið Sprint 86 | Staðfest af Sigvalda |
| 0.2 EEA UI wording í interfaces/*.html | ✅ Lokið Sprint 86 | Staðfest af Sigvalda |

## Sprint 89 Deferral Note

island.is CMS (Hæstiréttur + Persónuvernd + Dómstólar) frestað vegna:
- Paperwork bandwidth: 6+ open tracks (Mojeek DPA, Auðkenni, Straumur Kvika, LUMI, Vigfús, Alibaba H20)
- Outreach við Stafrænt Ísland krafist — Sprint 89 trigger: þegar Sigvaldi hefur bandwidth
- 3-for-1 deliverable bíður — island.is CMS unification (Lesson #105 candidate) stendur

---

## PHASE A — STATUS: ✅ FULL GREEN — Tilbúið fyrir Opus + Aðal Phase B review

Dagsetning: 17. maí 2026, 07:39
