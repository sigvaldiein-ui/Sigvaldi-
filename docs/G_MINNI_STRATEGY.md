# G_MINNI_STRATEGY.md — Verkefnataska og Dulkóðun

**Dags:** 11. júní 2026
**Höfundur:** Per #15 (bakendi)
**Staða:** Strategy — bíður Opus-GREEN

---

## 1. Aðskilnaður Geymslu
- **Hvelfingin:** Helst 100% RAM-only (`/dev/shm`). Engin varanleg vistun.
- **Verkefnataskan:** Ný viðvarandi geymsla á NVMe diski fyrir Erindrekann, dulkóðuð með AES-256-GCM.

## 2. Per-Tenant Scoping (Læsta herbergið)
- Hver áskrifandi (fyrirtæki/teymi) fær sitt eigið dulkóðaða svæði.
- SQLite grunnurinn (`mimir_core.db`) heldur utan um aðgangsstýringu. Teymi A getur undir engum kringumstæðum lesið minni Teymis B.
