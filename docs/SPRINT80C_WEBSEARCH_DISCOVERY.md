# SPRINT 80C WEB SEARCH – Discovery Phase
**Date:** 9. maí 2026
**Author:** Per, executor | **Reviewer:** Opus 4.7
**Status:** 🟡 Draft

## 1. Núverandi staða
| Atriði | Gildi |
|---|---|
| API lykill | MOJEEK_API_KEY i .env |
| Staða lykils | Virkur (inneign: £10) |
| Svarform | XML (JSON i bodi) |
| Islensk leit | Virkar |
| HTTP status | 200 OK |

## 2. Mojeek API – Taeknilegir eiginleikar
- Endapunktur: GET https://api.mojeek.com/search
- Breytur: api_key, q, fmt (xml/json)
- Takmarkanir: 10 nidurstodur/svar

## 3. Fyrirhugud samtthaetting
- Nytt tol: tools/search_web.py
- Flaedi: Notandi -> FastAPI -> Ef ytri gagna thorf -> Mojeek -> LLM med samhengi
- Kostnadur: £1–3/1000 fyrirspurnir

## 4. Ahaettur
| Ahaetta | Motvaegisadgerd |
|---|---|
| Inneign klarast | Eftirlit med stodu |
| API nidurtimi | Fallback a RAG eingongu |

## 5. Naestu skref
1. Proffa JSON svar
2. Hanna search_web.py
3. Skrifa strategy skjal
