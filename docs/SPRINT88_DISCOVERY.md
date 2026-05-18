# Sprint 88 — Phase A Discovery

**Dags:** 18. maí 2026
**Staða:** Phase 0 og Phase C PASS. Phase A empirical gögn safnað.

---

## A1 — Source Gate / Morphology

Núverandi fallbeygingarstuðningur byggir á einfaldri heuristik:
- `_extract_names`: finnur sérnöfn (hástafanafn + eftirnafn).
- `_name_root`: tekur fyrstu 5 stafi fyrsta nafns í lágstöfum.

**Styrkleikar:**
- Virkar fyrir nafnorð í nefnifalli (Daði Már, Kristrún Frostadóttir).
- Virkar fyrir aukaföll sem halda fyrstu 5 stöfum (Daða Má, Kristrúnu).

**Veikleikar:**
- `"Engin sérnöfn hér."` → gefur `['Engin']` (false positive).
- `Þorgerður → þorge`, `Þorgerði → þorge` — virkar, en ótryggt fyrir sjaldgæfari nöfn.
- `validate_and_retry` er **bypassað** (skilar `source_gate_bypass_sprint82`).

**Fyrirhuguð úrbót (Phase B):**
- Sækja BÍN gögn fyrir nafnorð til að fá áreiðanlegri fallbeygingarþekkingu.
- Virkja `validate_and_retry` með réttum viðmiðum.

---

## A2 — Per-source Latency

| Gagnagjafi | Miðgildi latency | Citations per kall | Athugasemd |
|-----------|-----------------|-------------------|------------|
| Alþingi | 130–214 ms | 1–5 | Hraðvirkt XML API |
| Stjórnarráðið | 354–615 ms | 11 | Stöðugt, mörg citations |
| Hagstofa | 559–905 ms | 2 | Þyngri, en áreiðanleg |
| Vísindavefur | 957–1390 ms | 0–1 | Hægastur, misjafnt coverage |

---

## A3 — End-to-end /api/chat RTT

| Fyrirspurn | Status | Latency | Citations | Athugasemd |
|-----------|--------|---------|-----------|------------|
| „Hver er íbúafjöldi á Íslandi 2026?" | 200 ✅ | 23.5 sek | 7 | Vitinn, eðlilegur tími |
| „Hver er verðbólga á Íslandi 2025?" | 200 ✅ | 29.5 sek | 6 | Vitinn, eðlilegur tími |
| „Hvað segir persónuverndarlög...?" | Timeout ❌ | 60.0 sek | — | RAG leit of þung — þarf skoða |

---

## Samantekt

- **Phase 0:** DEV virkar með `ALVITUR_DEV_MODE=1`, engin kvóta-blokkun, engin 500 villa.
- **Phase C:** Guard (`_validate_response`) er tengdur og empirical sannaður.
- **Phase A:** Öll empirical gögn safnað. Discovery doc tilbúið.

---

## Phase B — BÍN Integration (18. maí 2026)

| Verk | Staða |
|------|-------|
| BÍN wrapper skrifaður | ✅ `tools/sources/bin_wrapper.py` |
| `_name_root_bin` bætt við source_gate | ✅ Virkt, BÍN svarar rétt fyrir mannanöfn |
| `_validate_response` guard | ✅ Virkt í `handle_chat` |
| `validate_and_retry` | 🟡 By-pass-að — virkjast í síðari spretti |

## Phase C — Timeout lagfært (18. maí 2026)

| Verk | Staða |
|------|-------|
| SearchLawTool timeout | ✅ 10s → 30s |
| RAG fyrirspurnir klárast | ✅ 4 citations, 200 OK |

## Phase D — Hagstofa PX-Web (18. maí 2026)

| Verk | Staða |
|------|-------|
| API rannsókn | 🟡 Skilar `Bad Request` — þarfnast dýpri rannsóknar |

## Næstu skref — 19. maí 2026

| Forgangur | Verk |
|-----------|------|
| 1 | Rannsaka Hagstofu PX-Web með réttri API-slóð |
| 2 | Skoða reglugerd.is |
| 3 | Fínstilla vLLM — skoða hvort hægt sé að flýta svörum |

---

## Phase D — Hagstofa PX-Web (uppfært 18. maí 2026)

| Verk | Staða |
|------|-------|
| MAN00101 / MAN10001 (mannfjöldi) | ✅ Virkt — mannfjöldatölur frá Hagstofu með numeric snippets |
| VIS01000 (vísitala neysluverðs, verðbólga) | ✅ Lagfært API-path í `HAGSTOFA_API` (`Efnahagur/visitolur/1_vnv/1_vnv/VIS01000.px`), skilar numeric snippet fyrir verðbólgu |
| VIN01002 (atvinnuþátttaka, atvinnuleysi) | ✅ Nýtt table_id fyrir atvinnuleysi (`Samfelag/vinnumarkadur/vinnumarkadsrannsokn/3_arstolur/VIN01002.px`), skilar numeric snippet fyrir atvinnuleysi |
| LAN10001 (meðallaun) | ✅ Óbreytt í þessari lotu |

Empirical próf (Task 2):

- `fetch_hagstofa("verðbólga 2026", 5)` → `table_id=VIS01000`, `error=None`, `raw_count=2`, snippet áform: „Vísitala neysluverðs og breytingar — 683.8“.
- `fetch_hagstofa("atvinnuleysi 2026", 5)` → `table_id=VIN01002`, `error=None`, `raw_count=2`, snippet áform: „Atvinnuþátttaka, atvinnuleysi 1991–2025 — 81.0“.

---

## Phase E — Vísindavefur timeout (18. maí 2026)

| Verk | Staða |
|------|-------|
| `fetch_visindavefur` timeout | ✅ Lækkað úr 10s í 5s (`httpx.AsyncClient(timeout=5)`) |
| Error-handling | ✅ Heldur áfram að skila `{"citations": [], "error": "timeout"}` án þess að blokkera /api/chat |
| Orchestrator | ✅ `search_web_multi.py` keyrir Vísindavef samhliða öðrum sources með `asyncio.gather` og fær partial results ef Vísindavefur tímast út |

Empirical próf (Task 3):

- Beint kall: `fetch_visindavefur("hantaveira", 5)` → `elapsed_s ≈ 1.15s`, `raw_count=1`, `error=None`, citations=1 (rétt Vísindavefur-svar).
- Þetta tryggir að Vísindavefur blokkerar ekki lengur heila /api/chat beiðni í átt að 60s timeout; aðrir sovereign/official sources (Hagstofa, Alþingi, Stjórnarráð) ná alltaf að skila.

