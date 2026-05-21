# 🏛️ ADR-007a: Server-Side RAG Orchestration

**Staða:** Samþykkt (Ígildi tagg: `v96-trust-boundary-server-rc1`)

## Samhengi
Til að tryggja gagnaöryggi og koma í veg fyrir að viðkvæmar leitarfyrirspurnir eða hrátt samhengi (context) fari í gegnum biðlara (client), þarf að færa alla RAG-leit inn fyrir traustmörkin (trust boundary) á bakendanum. Slóðin á Qdrant hefur verið færð yfir í `/workspace/Sigvaldi-/data/qdrant_laws_v2`.

## Ákvörðun
Innleiða `auth_and_search` fallið beint í bakendanum sem millilag áður en streymi hefst:
1. Sækja `identity_token` úr líkama beiðnarinnar (`body_data`).
2. Túlka og auðkenna notanda (notast við "anonymous" ef token vantar í DEV).
3. Keyra leit beint á bakenda í gegnum `SearchLawTool()` við Qdrant-gagnagrunninn áður en `StreamingResponse` skilar niðurstöðu.

## Afleiðingar
* **Kostir:** Ekkert hrátt samhengi eða IP-tengingar við gagnagrunna leka til client-hliðar.
* **Gallar:** Meiri vinnsla og minnisnotkun á miðlægum bakenda við hverja beiðni.
