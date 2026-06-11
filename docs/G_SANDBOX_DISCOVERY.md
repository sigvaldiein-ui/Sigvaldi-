# G_SANDBOX_DISCOVERY.md — Einangrun kóða-keyrslu fyrir Erindrekann

**Dags:** 11. júní 2026
**Höfundur:** Per #15 (bakendi)
**Staða:** Discovery — bíður Opus-GREEN áður en strategía er skrifuð

---

## 1. Einangrunar-möguleikar á H20

| Tól | Staða | Athugasemd |
|-----|-------|------------|
| Docker | ✅ Uppsett (v29.5.2) | Styður container-einangrun |
| gVisor/runsc | ❌ Ekki uppsett | Þarf að setja upp fyrir harða einangrun |
| nproc | 16 CPU kjarnar | Nóg af CPU fyrir sandkassa |
| Minni | 91 GB (86 GB laust) | Nóg af minni fyrir sandkassa |
| GPU | Fullur af Qwen (89 GB) | Sandkassar keyra á CPU |

---

## 2. Öryggiskröfur fyrir kóða-keyrslu

| Krafa | Staða | Athugasemd |
|-------|-------|------------|
| Einangrun frá hýsil-skráakerfi | 🟡 Docker nær grunni, gVisor er harðara |
| Einangrun frá .env / lyklum | 🟡 Docker container hefur ekki aðgang að .env sjálfgefið |
| Einangrun frá neti (engin egress) | 🟡 Docker netið getur verið lokað (`--network none`) |
| Resource limits (CPU/minni) | ✅ Docker styður `--cpus` og `--memory` |
| Ferskt umhverfi per keyrslu | ✅ Docker container ræstur og fjarlægður eftir hverja keyrslu |

---

## 3. Valkostir fyrir sandkassa

### Valkostur A — Docker með `--network none`
- **Kostir:** Þegar uppsettur, einfalt, hratt
- **Gallar:** Veikari einangrun en gVisor (deilir kjarna með hýsli)
- **Hentar:** Fyrstu útgáfu, ef kóði er yfirfarinn

### Valkostur B — gVisor/runsc (harðari sandkassi)
- **Kostir:** Sterkari einangrun, sér kjarni, öruggara fyrir óþekktan kóða
- **Gallar:** Þarf að setja upp, aðeins hægara
- **Hentar:** Production umhverfi fyrir vibe-coding

### Valkostur C — VM/microVM
- **Kostir:** Fullkomin einangrun
- **Gallar:** Of þungt fyrir H20, ekki raunhæft á einni vél
- **Hentar:** Ekki fyrir H20

---

## 4. Tilögur

1. **V1 (núna)** → Docker með `--network none`, `--cpus=2`, `--memory=2g`. Ferskt container per keyrslu.
2. **V2 (production)** → gVisor/runsc. Setja upp þegar Erindrekinn fer í alvöru beta.
3. **Öryggisregla:** Engin tenging úr sandkassa að `.env`, OpenRouter lykli, eða Qdrant. Aðeins skilgreint API.

---

## 5. Næstu skref

- Opus-GREEN á þetta discovery skjal
- Strategía: velja Valkost A fyrir V1, undirbúa Valkost B fyrir V2
- Útfærsla: Docker sandkassi með `--network none`
