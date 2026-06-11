# G_MINNI_DISCOVERY.md — Geymslu-kortlagning fyrir Erindrekann

**Dags:** 11. júní 2026
**Höfundur:** Per #15 (bakendi)
**Staða:** Discovery — bíður Opus-GREEN áður en strategía er skrifuð

---

## 1. Núverandi geymsla á H20

| Geymsla | Staðsetning | Stærð | Tegund | Notkun í dag |
|----------|--------------|--------|--------|---------------|
| SSD aðal-disks | `/dev/nvme0n1p3` | 148 GB (95 GB laust) | NVMe SSD | Allt — kóði, gögn, geymsla |
| `/workspace` | `/dev/nvme0n1p3` | 47 GB notað | Varanlegt | Qdrant geymsla (161 MB), kóði, skjöl |
| `/dev/shm` | tmpfs | 46 GB (4 KB notað) | RAM, hverfult | Hvelfingin (zero-disk) |
| Qdrant | `/workspace/Sigvaldi-/data/qdrant_laws_v2` | 161 MB | Varanlegt á disk | Lagasafnið (alvitur_laws_v2) |
| Hvelfingin | `/dev/shm/alvitur_zero_disk` | 0 bæti (hverfult) | RAM, eytt við restart | Trúnaðarskjöl (sealed vault) |

---

## 2. Dulkóðunarmöguleikar

| Tól | Staða | Athugasemd |
|-----|-------|------------|
| `cryptography` pakki | ✅ Uppsettur | Styður AES-256-GCM, Fernet, PBKDF2 |
| AES-256-GCM | ✅ Virkar | 256 bita lyklar, authenticated encryption |
| Lyklastjórnun | 🟡 Óbyggð | Engin KMS — lyklar þurfa örugga geymslu |

---

## 3. Per-tenant scoping

| Atriði | Staða |
|--------|-------|
| `tenant_id` í db_manager.py | ✅ Skilgreint í mimir_core.db |
| Qdrant per-tenant söfn | ✅ Hægt að búa til ný söfn per tenant |
| Aðgangsstýring | 🟡 Engin per-tenant einangrun í dag |
| Læst herbergi | ❌ Ekki til — þarf nýsmíði |

---

## 4. Valkostir fyrir Verkefnatöskuna (dulkóðuð, viðvarandi geymsla)

### Valkostur A — Qdrant með dulkóðuðum payloads
- **Kostir:** Þegar uppsett, styður söfn per tenant, vector-leit innbyggð
- **Gallar:** Dulkóðun per skjal í payload, ekki native dulkóðun-at-rest
- **Hentar:** Minnislag Erindrekans (archival/semantic memory)

### Valkostur B — Skráarkerfi með AES-256-GCM
- **Kostir:** Full dulkóðun-at-rest, óháð Qdrant
- **Gallar:** Þarf sér API, engin innbyggð leit
- **Hentar:** Verkefnataskan (skjöl, kóði, drög)

### Valkostur C — Hybrid (Qdrant + dulkóðað skráarkerfi)
- **Kostir:** Best of both — Qdrant fyrir leit, dulkóðaðar skrár fyrir gögn
- **Gallar:** Flóknari, tvö kerfi að stjórna
- **Hentar:** Full G-MINNI útfærsla

---

## 5. Tilögur

1. **Minnislag Erindrekans** → Qdrant (Valkostur A). Þegar uppsett, styður söfn per tenant.
2. **Verkefnataskan** → Dulkóðað skráarkerfi (Valkostur B). AES-256-GCM, per-tenant lyklar.
3. **Læst herbergi** → Hybrid (Valkostur C). Qdrant fyrir leit, dulkóðaðar skrár fyrir gögn.
4. **Lyklastjórnun** → Sér KMS eining. Lyklar geymdir í `.env`, ekki í git. Róteraðir per tenant.

---

## 6. Næstu skref

- Opus-GREEN á þetta discovery skjal
- Strategía: velja arkitektúr (A/B/C) fyrir hverja geymslu
- Útfærsla: byggja per-tenant dulkóðun + Qdrant söfn
