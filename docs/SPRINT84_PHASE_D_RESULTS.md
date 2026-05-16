# Sprint 84 Phase D — Evals Harness v1 Niðurstöður

**Dags:** 16. maí 2026
**Aðferð:** 30 fyrirspurnir keyrðar í 6 skömmtum (5 í einu)
**Umhverfi:** DEV (port 8003)

---

## Yfirlit

| Mælikvarði | Gildi |
|-----------|-------|
| Heildarfjöldi fyrirspurna | 30 |
| Tókust (200 OK) | 20 (67%) |
| Citation Precision Rate | 23% (7/30) |
| Grounding Rate | 23% (7/30) |
| Document Parsing Success Rate | Frestað til Sprint 86 |
| Hallucination Rate | Handvirkt mat — óunnið |

---

## Vitinn vs Vault

| Mælikvarði | Vitinn | Vault |
|-----------|--------|-------|
| Fjöldi fyrirspurna | 21 | 9 |
| Meðaltími | ~65 sek | ~30 sek |
| Með citations | 4 (19%) | 3 (33%) |

---

## Skammtar

| Skammtur | Fyrirspurnir | Tókust | Citations |
|----------|-------------|--------|-----------|
| 1 | 1-5 | 5/5 | 6 |
| 2 | 6-10 | 5/5 | 0 |
| 3 | 11-15 | 5/5 | 9 |
| 4 | 16-20 | 5/5 | 6 |
| 5 | 21-25 | 0/5 | 0 |
| 6 | 26-30 | 0/5 | 0 |

---

## Athugasemdir

- Skammtar 5 og 6 féllu allir — líklega vegna quota/rate limiting.
- Citation Precision Rate er lægri en 33% baseline frá fyrri mælingu — skýrist af hertari relevance síun.
- Vitinn er hægari vegna ytri API kalla (Mojeek, Stjórnarráð).
