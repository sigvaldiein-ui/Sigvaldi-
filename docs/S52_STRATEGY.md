# S5-2 STRATEGY — Réttindastýring Leið 1 (fail-CLOSED)

**Dags:** 12. júní 2026
**Höfundur:** Per #15
**Staða:** Strategy — bíður Opus-GREEN
**Byggir á:** S52_DISCOVERY.md (GREEN)

---

## 1. Hönnunarmarkmið

**FAIL-CLOSED.** Óþekktur/óvirkur sub → 401/403, ALDREI fallback á JWT claims.
org_id og tier koma eingöngu úr gagnagrunni, aldrei úr token.

## 2. Middleware flæði

Request → JWT verify → fletta sub í users töflu →
  - sub ekki í töflu → 403
  - active=0 → 403
  - DB niðri → 503 (fail-closed)
  - fannst + active=1 → payload.org_id = DB.org_id, payload.tier = DB.tier

## 3. Villuleiðir

| Atburður | HTTP | Skilaboð |
|----------|------|----------|
| sub tómt eða óþekkt | 403 | Forbidden |
| active=0 | 403 | Account disabled |
| DB niðri | 503 | Service Unavailable |

## 4. Cache

TTL <= 60s, invalidation við notenda-breytingu.

## 5. Async útfærsla

aiosqlite í async middleware. Uppfletting <5ms.

## 6. Innleiðingarskref

1. Strategy GREEN frá Opus
2. Útfæra middleware með fail-closed rökfræði
3. Prófa cross-org: rangt org_id í claims → org_id úr DB
4. Prófa óþekkt sub → 403
5. Prófa DB niðri → 503
