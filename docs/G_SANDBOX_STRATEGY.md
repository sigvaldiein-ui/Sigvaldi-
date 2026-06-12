# G_SANDBOX_STRATEGY.md — Einangrun á kóðakeyrslu

**Dags:** 11. júní 2026
**Höfundur:** Per #15 (bakendi)
**Staða:** Strategy — bíður Opus-GREEN

---

## 1. Docker V1 Útfærsla
Allur kóði sem Erindrekinn skrifar sjálfur eða fær frá notanda (Vibe-coding) MÁ EKKI keyra á aðalhýslinum (H20).

## 2. Hörð Mörk (Constraints)
Sandkassinn verður spunninn upp með eftirfarandi Docker flöggum:
- `--network none`: Algjörlega klippt á netið. Engin leið að leka gögnum eða kalla í ytri API.
- `--cpus=2`: Takmarkað reikniafl til að verja Qwen módelið.
- `--memory=2g`: Takmarkað vinnsluminni.
- Umhverfisbreytur (`.env`) og API lyklar hýsilsins verða ekki mountaðir.
