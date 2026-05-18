# Sprint 89 — Phase 0 Discovery

**Dags:** 18. maí 2026  
**Staða:** Phase 0 empirical baseline skráð. Phase A citations-regression endurmetin eftir port-staðfestingu.

---

## Markmið

Markmið Sprint 89 er að loka V1 quality bar með empirical sönnun fyrir:
- citations > 0 á 6-query eval í DEV,
- p95 < 30 sekúndur,
- 0 uppspuna (hallucinations),
- og bæta BÍN query-expansion í retrieval pipeline.

---

## Mikilvæg leiðrétting frá Sprint 88 lokun

Við upphaf Sprint 89 leit út fyrir að DEV-mode væri með `citations=0` á öllum 6 queries.  
Empirical endurpróf sýndi að það var **ekki kóða-regression**, heldur **rangt port í eval-skripti**:

- Port `8000` skilaði hraðri svörun með `citations=0`.
- Raunverulegt DEV instance fyrir Vitann var á porti `8003`.
- Þegar sama 6-query eval var keyrt á `8003` komu citations aftur á öllum 6 queries.

Niðurstaða: alleged DEV citations-regression var í raun **ops/config mismatch**, ekki staðfest Python regression.

---

## Phase 0 — 6-query baseline á réttu DEV porti (8003)

| Q | Fyrirspurn | RTT | Citations | Hallucinated | Athugasemd |
|---|---|---:|---:|---|---|
| 1 | Hver er íbúafjöldi á Íslandi 2026? | 6277 ms | 7 | False | PASS |
| 2 | Hver er verðbólgan á Íslandi núna? | 36915 ms | 7 | False | Citations til staðar, latency yfir markmiði |
| 3 | Hver er atvinnuleysið á Íslandi? | 53239 ms | 8 | False | Citations til staðar, latency hátt |
| 4 | Hvað segja persónuverndarlög um lífkennaupplýsingar? | 68478 ms | 4 | False | Vault-like lögfræði query enn þung |
| 5 | Hvernig virka skattaívilnanir fyrir kvikmyndaiðnað á Íslandi? | 19698 ms | 5 | False | PASS |
| 6 | Hvað eru hantaveirur? | 31855 ms | 2 | False | Citations til staðar, yfir latency markmiði |

---

## Túlkun

### Það sem baseline sannar

- **Citations regression í DEV er ekki staðfest** þegar keyrt er á rétta portinu (`8003`).
- **0 uppspuni** í öllum 6 baseline fyrirspurnum samkvæmt núverandi lexical smoke-check.
- Retrieval og source-pipeline virðast því virka í DEV þegar hitt er á rétta instance.

### Það sem baseline sýnir enn sem vandamál

- **Latency markmið Sprint 89 er ekki enn náð.**
- p95 er langt yfir 30 sekúndum; þyngstu fyrirspurnir eru:
  - atvinnuleysi (~53.2 sek),
  - persónuverndarlög / lífkennaupplýsingar (~68.5 sek),
  - hantaveirur (~31.9 sek).

---

## Ályktun eftir Phase 0

Sprint 89 þarf ekki að byrja á "citations=0" bugfix í DEV-mode.  
Í staðinn færist megináhersla yfir á:

1. latency greiningu og hugsanlega tier-/source-cost optimization,
2. BÍN query-expansion í retrieval pipeline,
3. prompt/pipeline samræmingu milli Vitans og Hvelfingar.

Vault-tier persónuverndarlög query er áfram sérstaklega áhugaverð vegna hárrar RTT og verður skoðuð nánar í næstu phase.

---

## Næstu skref

| Forgangur | Verk |
|---|---|
| 1 | Staðfesta `general` vs `vault` hegðun fyrir persónuverndarlög / lífkennaupplýsingar |
| 2 | Hanna BÍN query-expansion í `tools/search_web_multi.py` |
| 3 | Endurkeyra 6-query eval eftir latency/query-expansion breytingar |

