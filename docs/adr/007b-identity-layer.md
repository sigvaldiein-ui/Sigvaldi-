# 🏛️ ADR-007b: Identity Layer & Middleware Scope Expansion

**Staða:** Samþykkt (Ígildi tagg: `v97-identity-layer-rc1`)

## Samhengi
Það vantaði miðlæga, örugga og ófrávíkjanlega auðkenningu á alla innri endapunkta (`/api/`) til að styðja við þjónustustig (tiers) og tryggja ríkisöryggi á gögnum Alviturs.

## Ákvörðun
Innleiða `IdentityMiddleware(BaseHTTPMiddleware)` sem keyrir á öllum `/api/` köllum (fyrir utan `/api/health`):
1. **Fail-CLOSED:** Ef `Authorization: Bearer <token>` vantar eða er rangt, lokar kerfið samstundis með `401 Unauthorized`.
2. **Dulkóðun:** Notast eingöngu við **RS256** reikniritið með `JWT_PUBLIC_KEY`.
3. **Stöðuútdeiling:** Sækir sjálfkrafa `sub`, `org_id` og `tier` (sjálfgefið "Vitinn") og geymir í `request.state.user_claims`.

## Afleiðingar
* **Kostir:** Algjört öryggi, engin hætta á opnum endapunktum fyrir mistök.
* **Gallar:** Prófanir í DEV krefjast gildra eða gildra gervitákna (dummy keys).
