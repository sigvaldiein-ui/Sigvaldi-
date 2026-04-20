# Alvitur — Status

**Síðast uppfært:** 2026-04-20 18:10 UTC
**Núverandi útgáfa:** v0.61-fasi-a
**Commit:** 338ce19
**Sprint:** 61 Fasi A — KLÁRAÐ ✅

## Núverandi arkitektúr

### Leið A — General tier (cloud)
- OpenRouter chain: Haiku → Sonnet → gpt-4o-mini
- ZDR enabled (`OPENROUTER_ZDR_CONFIRMED=true`)
- Deepseek polish layer á úttaki
- Notað fyrir almennar fyrirspurnir

### Leið B — Vault tier (sovereign)
- Local vLLM: `qwen3-32b-awq` á `localhost:8002`
- Keyrir á íslenskri GPU (Runpod pod)
- ENGIN cloud fallback — 503 ef niðri
- 413 gate ef input > 7000 tokens
- Notað fyrir trúnaðargögn

## API endpoints

| Endpoint | Tier routing | Response field |
|----------|-------------|---------------|
| `/api/chat` | `tier` param | `pipeline_source` |
| `/api/analyze-document` | `X-Alvitur-Tier` header | `pipeline_source` |
| `/api/health` | N/A | `status`, `version` |

## Sovereign guarantees (live tested)

- ✅ Vault data never leaves Icelandic GPU
- ✅ Response includes `pipeline_source` audit field
- ✅ Local module down → 503, never silent cloud fallback
- ✅ Oversized vault input → 413, never silent truncation

## Gæði

- Leið A (Haiku): A+ íslenska, ~2s svör
- Leið B (Qwen3-32B): B+ íslenska, ~6s svör
- Leið B batnar verulega með document context

## Næstu skref

### Fasi B (UX polish)
- Loading states í UI
- Error messages á íslensku
- Admin dashboard fyrir pipeline_source stats

### Fasi C (Qwen3 quality)
- Fine-tune á íslensku dataseti (A+ markmið)
- A100 upgrade fyrir max_model_len 16384
- Hraða target: Leið B ~3s

### Fasi D (Beta)
- 3-5 early adopters
- Feedback loop
- Sovereign marketing launch

## Backups á pod

- `interfaces/config.py.bak-fallback-1505`
- `interfaces/web_server.py.bak-fallback-1505`
- `interfaces/chat_routes.py.bak-fallback-1800`

## Rollback

```bash
git revert 338ce19   # eða
git checkout 7ef7332 -- interfaces/
```
