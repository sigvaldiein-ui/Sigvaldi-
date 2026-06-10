# DESIGN_VITINN — Vitinn með tveimur óháðum hökum

**Frá:** Opus 4.8 (gatekeeper / strategisti)
**Til:** Sigvaldi (CTO/HITL), Per (bakendi), Hönnuður (framendi)
**Staða:** DESIGN — GREEN-að af CTO 10. júní 2026
**Byggir á:** GATE_STARFSMADUR_OG_VITI3.md (GREEN)

## 1. Kjarnahugmynd
Vitinn er rannsóknardeildin. Tvö óháð hök stýra því hve langt fyrirspurnin fer út:

- [ ] Leita líka á vefnum — Staan/Mojeek ytri leit
- [ ] Virkja Stórmeistara — frontier-líkan gegnum OpenRouter ZDR

**Bæði óhökuð = 100% sovereign:** aðeins frysta lagasafnið (Qdrant) + local Qwen, ekkert fer út.

## 2. Fjórar samsetningar
| Vefur | Stórmeistari | Útkoma |
|-------|--------------|--------|
| ❌ | ❌ | Qdrant + Qwen. Sovereign, hratt, ódýrt |
| ✅ | ❌ | Qdrant + Staan/Mojeek + Qwen |
| ❌ | ✅ | Qdrant-samhengi → frontier |
| ✅ | ✅ | Qdrant + vefur + frontier. Hæsti kostnaður |

## 3. Öryggis-leiðrétting
Báðar ytri leiðir eru egress. PII-þvottur þarf á báðar:
- Vefleit: gegnum PII Sentry áður en hún fer til Staan/Mojeek
- Stórmeistari: fyrirspurn + samhengi gegnum PII Sentry
- Báðar: aðeins ZDR providerar

Ein PII-gátt, tveir egress-neytendur.

## 4. Fasar og gáttir
| Fasi | Verk | Gátt |
|------|------|------|
| F-VITI-0 | Discovery: search_web_multi | Opus GREEN |
| F-VITI-1 | Tvö hök: mockup → kóði | Opus GREEN |
| F-VITI-2 | Vefleitar-egress (háð F1) | Opus GREEN |
| F-VITI-3 | Stórmeistari (háð F1) | Opus GREEN |
| F-VITI-4 | Vörður-stilling | Opus GREEN |

## 5. Acceptance
- Bæði óhökuð → engin ytri köll (núll útumferð)
- Vefur hakað → sanitized fyrirspurn til Staan
- Stórmeistari hakað → consent-gluggi + ZDR provider
- Sovereign-leiðin óbreytt frá því sem virkar í dag

**Ekkert egress fer í loftið fyrr en F1 (PII Sentry) er GREEN.**
