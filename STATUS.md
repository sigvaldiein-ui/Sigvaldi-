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

## Sprint 61.3 Hotfix — vLLM context length (2026-04-21 07:13 UTC)

**Vandamál:** Reikningsyfirlit (8 bls. Excel, 6693 tokens) hristist á vault
tier — vLLM var með `--max-model-len 8192`, request 6693+1500=8193 → 503.

**Lausn:** Endurræsa vLLM með `--max-model-len 32768`.
- VRAM: 41.6/46 GB (90% — sama sem fyrr)
- KV cache: 82,896 tokens → 2.53x concurrency headroom
- Native Qwen3-32B supports 40,960 → vel innan sviðs

**Skjalastærð sem nú virkar á vault:**
- Einfaldur texti: allt að ~24 bls.
- Excel með töflum: allt að ~12-16 bls.

**Startup script:** `/workspace/start_vllm_32k.sh` skrifaður fyrir
endurkeyrslu eftir pod restart.

**Ekki kóðabreyting — bara vLLM flag.**
Semaphore(1) + rule-based vault classify enn í gildi.

## Sprint 61.4 Hotfix — httpx timeout (2026-04-21 07:45 UTC)

**Vandamál:** Eftir Sprint 61.3 (32k context), vault path á stórum skjölum
(>7k input tokens) hristist með `ReadTimeout` eftir 60 sek — httpx.AsyncClient
default timeout í web_server/chat_routes var 60s.

Live timeline:
- 07:29:49 UI analyze-document vault request kemur (10k+ tokens skjal)
- 07:30:49 web_server ReadTimeout eftir nákvæmlega 60 sek
- 07:35:38 vLLM náði að klára sama request (94 sek total)
- → Fix: lengja httpx timeout í 180s

**Lausn:** `httpx.AsyncClient(timeout=180.0)` á vault path.

**Live verified 2026-04-21 07:45:**
- in=10,406 out=598 HTTP 200 á raunverulegt reikningsyfirlit
- pipeline_source: local_vllm_qwen3-32b-awq (sovereign)

**Backups:** `*.bak-timeout-0740`

## 🏆 SPRINT 61 COMPLETE — 2026-04-21 08:14 UTC

### Production-Verified Sovereignty
Qwen3-32B-AWQ sovereign (vault tier) live-verified á raunverulegu
reikningsyfirliti (196 rows, Excel, ~10,400 tokens input).
Niðurstaða: 19 flokkaðir kostnaðarliðir á íslensku, ítarlegri
en Claude 3.5 Haiku (5 flokkar) á sömu gögnum.

**Quality > Cloud á icelandic finance analysis.**

### 5 Tags Shipped (16 klst)
| Tag | Hvað |
|-----|------|
| v0.61-fasi-a | Sovereign Leið B online |
| v0.61.1-hotfix-sovereignty | ClassifySkill rule-based (0 cloud leak) |
| v0.61.2-hotfix-concurrency | Semaphore(1) OOM guard |
| v0.61.3-hotfix-context | vLLM 8k → 32k context |
| v0.61.4-hotfix-timeout | httpx 60s → 180s timeout |

### Sovereignty Stack (Live)
- ClassifySkill rule-based (no LLM call on vault path)
- Semaphore(1) vault serialization
- Qwen3-32B-AWQ @ 32k context
- httpx timeout 180s (real-world headroom)
- 0 bytes til OpenRouter á vault (verified via call counter)

### Performance Envelope
- Small (< 1k tokens): 7-10 sec
- Medium (5k tokens): 20-30 sec
- Large (10k+ tokens, 196-row Excel): 30-60 sec
- Max timeout: 180 sec

### Live Milestone
- alvitur.is live á internetinu
- Fyrsti utanaðkomandi notandi kom óvænt kl 07:55 UTC
- Kerfi skilaði greining án issues
- → Rate limiting → Sprint 62 P0

### Next: Sprint 62 Hardening
1. Rate limiting per IP
2. RAG embeddings audit
3. Log sanitization
4. Telemetry audit
5. Sentry before_send hook
6. _polish import fix
7. UI loading indicator fyrir vault

---
