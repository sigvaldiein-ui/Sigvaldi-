# S5-2 DISCOVERY — Réttindastýring Leið 1

**Dags:** 12. júní 2026
**Höfundur:** Per #15
**Staða:** Discovery — bíður Opus-GREEN

---

## 1. Núverandi staða

JWT token er staðfestur í middleware, en `sub`, `org_id`, `tier` eru dregin BEINT úr JWT claims án nokkurs lookup í gagnagrunni. Engin notendatafla er til í neinum af gagnagrunnunum á H20 (state_store.db, alvitur.db, mimir_core.db).

## 2. Vandamálið (úr ÚTTEKT-1)

Token með `org_id="annad-fyrirtaeki"` fékk scope þess fyrirtækis. Token með `tier="Hvelfingin"` komst gegnum tier-gátt. Middleware treystir JWT claims blint.

## 3. Tillaga

Ný `users` tafla í state_store.db með `sub`, `org_id`, `tier`, `role`, `active`. Eftir JWT-staðfestingu flettir þjónninn `sub` upp í töflu og sækir ÞAÐAN org_id, tier og hlutverk. Claims úr token eru aldrei heimild. Óþekktur sub → 403. DB niðri → 503 fail-closed.

## 4. Næstu skref

Opus GREEN → Strategy → Útfærsla
