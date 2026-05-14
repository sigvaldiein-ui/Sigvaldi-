# Sprint 80c v2 – Lokaskýrsla 12. maí 2026

## Kerfisstaða
✅ alvitur.is – HTTP 200 (Vitinn + Hvelfingin)
✅ API /api/chat – Virkar
✅ API /api/analyze-document – Virkar
✅ Multi-source RRF – Stjórnarráð + Stjórnartíðindi + Mojeek
✅ vLLM / Qwen3-32B AWQ – localhost:8002
✅ Qdrant v2 – 23.621 chunks
✅ Cloudflare – Skyndiminni hreinsað, rétt skrá send út

## Klárað
| # | Verk | Staða |
|---|------|-------|
| 1 | Mojeek API lykill + DPA | ✅ |
| 2 | Multi-source RRF (search_web_multi) | ✅ |
| 3 | Stofnagreining (stjornarradid_source.py) | ✅ |
| 4 | Temperature 0.0 í vLLM köllum | ✅ |
| 5 | Heimildagátt (source_gate.py) | ✅ Skrifuð, aftengd Leið A, færð til Sprint 82 |
| 6 | SOVEREIGNTY_AUDIT.md með Mojeek kafla | ✅ |
| 7 | Vitinn/Hvelfingin flipanöfn uppfærð | ✅ |
| 8 | app.js hotfix – texti → /api/chat | ✅ |
| 9 | JavaScript brennt í index.html (bakdyraleið) | ✅ |

## Þekkt vandamál
| # | Vandamál | Áætlun |
|---|----------|--------|
| 1 | Módelið skáldar fyrir fyrirspurnir án heimilda | Sprint 82 – Honest Data Gap |
| 2 | Hvelfingin flipi óvirkur í vafra | Bíður beta-prófana |
| 3 | Rauntímaleit (klukka) ekki virk | Sprint 83 |
| 4 | Vefþjónn óstöðugur við endurræsingu | Sprint 81 |

## Næstu skref – Sprint 81
| # | Verk |
|---|------|
| 1 | Systemd ferlastjóri fyrir Uvicorn |
| 2 | Cache busting með hash filenames |
| 3 | Cloudflare API purge automation |
| 4 | Dev/prod aðskilnaður (port 8003) |
| 5 | FastAPI Cache-Control middleware |

## Lærdómar
| # | Lærdómur |
|---|----------|
| 78 | Engin Python strengja-parsing í bash heredoc |
| 86 | Broad try/except getur falið NameError í 30+ klst |
| 87 | Temp 0.0 + HEIMILDIR merkingar = strong RAG anchoring |
| 88 | Stofnagreining (fyrstu 5 stafir) virkar fyrir íslenska titla |
| 89 | StaticFiles mount tekur forgang yfir sérstaka endapunkta – raða verður rétt |
