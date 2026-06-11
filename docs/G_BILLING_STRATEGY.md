# G_BILLING_STRATEGY.md — Token-mæling og áskriftarstefna

**Dags:** 11. júní 2026
**Höfundur:** Per #15 (bakendi)
**Staða:** Strategy — bíður Opus-GREEN

---

## 1. Token-mæling í AgentLoop

- Hvert LLM kall skráir `prompt_tokens` og `completion_tokens`
- Stórmeistara-köll (OpenRouter) skrá að auki kostnað í USD
- Allt skráð í audit-log með `tenant_id`, `task_id`

## 2. Loop-vörn

| Stilling | Sjálfgefið | Lýsing |
|----------|-----------|--------|
| MAX_STEPS | 10 | Hámarksfjöldi skrefa per verkefni |
| MAX_TOKENS | 50.000 | Hámarksfjöldi tokens per verkefni |
| MAX_COST_USD | 0.50 | Hámarkskostnaður per verkefni |

Þegar einhverju marki er náð:
1. Lykkjan frýs
2. Beiðni fer í HITL biðröð
3. Notandinn sér: „Verkefnið hefur náð hámarki. Viltu halda áfram?"

## 3. Qwen vs Stórmeistari — kostnaðar-aðgreining

| Líkan | Kostnaður | Telst gegn áskrift? |
|-------|-----------|---------------------|
| Qwen (local) | 0 USD | Nei — innifalið |
| Claude Sonnet 4.6 | ~$0.003/1K tokens | Já — dregið frá token-kvóta |
| Claude Opus 4.6 | ~$0.015/1K tokens | Já — dregið frá token-kvóta |

## 4. Áskriftarþrep

| Þrep | Verð | Qwen | Stórmeistari |
|------|------|------|--------------|
| Brons | Ókeypis | Ótakmarkað | 50/mán |
| Silfur | $29/mán | Ótakmarkað | 500/mán |
| Gull | $99/mán | Ótakmarkað | 2.000/mán |
