# SPRINT87_STRATEGY.md
**Dagsetning:** 17. maí 2026 — Phase B Strategy Doc
**Aðal rulings:** 6/6 locked | **Opus:** GREEN

---

## 1. Overview

**Sprint 87 thesis:** Setja upp Hagstofa PX-Web integration + Lesson #104 routing redesign
til að auka íslenska sovereignty share í Alvitur svörum.

**Scope:** Internal-only. Engar external negotiations. Engin island.is CMS (→ Sprint 89).

**Success criteria:**
- Hagstofa gögn birtast í Alvitur svörum með réttum citations (table_id + accessed_at + URL)
- Routing sendir íslenskar queries á íslenskar heimildir first
- `<think>` tags leka ekki í notendaviðmót
- Tag v87-routing-rc1 sett

---

## 2. Source Registry Design (D2)

**Skrá:** `config/source_registry.json`
**Validation:** Pydantic við server startup — fail-fast (blokkar boot ef invalid)
**Hot-reload:** Restart-required í V1 (hot-reload Sprint 88+)

```json
{
  "sources": [
    {
      "id": "althingi",
      "tier": 2,
      "access_pattern": "xml_api",
      "base_url": "https://www.althingi.is/altext/xml/",
      "rate_limit_rps": 1,
      "cache_ttl_hours": 24,
      "license": "public_domain",
      "attribution": "Alþingi Íslands"
    },
    {
      "id": "hagstofa",
      "tier": 2,
      "access_pattern": "hybrid_qdrant_dynamic",
      "base_url": "https://px.hagstofa.is",
      "rate_limit_rps": 1,
      "cache_ttl_hours": 24,
      "license": "CC_BY_4.0",
      "attribution": "Hagstofa Íslands"
    },
    {
      "id": "visindavefur",
      "tier": 2,
      "access_pattern": "html_search",
      "base_url": "https://www.visindavefur.is/search.php",
      "rate_limit_rps": 1,
      "cache_ttl_hours": 24,
      "license": "unknown",
      "attribution": "Vísindavefur Háskóla Íslands"
    },
    {
      "id": "stjornarradid",
      "tier": 2,
      "access_pattern": "html_search",
      "base_url": "https://www.government.is",
      "rate_limit_rps": 1,
      "cache_ttl_hours": 24,
      "license": "public_domain",
      "attribution": "Stjórnarráð Íslands"
    },
    {
      "id": "stjornartidindi",
      "tier": 2,
      "access_pattern": "html_search",
      "base_url": "https://www.stjornartidindi.is",
      "rate_limit_rps": 1,
      "cache_ttl_hours": 24,
      "license": "public_domain",
      "attribution": "Stjórnartíðindi"
    },
    {
      "id": "mojeek",
      "tier": 3,
      "access_pattern": "rest_api",
      "base_url": "https://www.mojeek.com/search",
      "rate_limit_rps": 2,
      "cache_ttl_hours": 6,
      "license": "commercial",
      "attribution": "Mojeek"
    }
  ]
}
```

---

## 3. Routing Redesign (D3 + D4)

**Pattern:** Tier-first lock í agent_core_v4.py — chat_routes er þunnur FastAPI only.


**Mojeek demotion:**
- Vitinn: RRF weight 0.3 (vs Tier 2: 0.7)
- Vault: explicit bypass — Mojeek kallað aldrei
- Citation flag: `"sovereign": false` á Mojeek results

---

## 4. Hagstofa Hybrid Architecture (D1)

**Tvær lagnir:**


**Citation format:**
```json
{
  "source": "hagstofa",
  "table_id": "VIS01000",
  "title": "Vísitala neysluverðs",
  "accessed_at": "2026-05-17T07:57:00Z",
  "url": "https://px.hagstofa.is/pxis/api/v1/is/Efnahagur/visitolur/VIS01000"
}
```

---

## 5. RRF + Dedup Design (D5)

**RRF formula:** score(d) = Σ 1/(k + rank(d)) þar sem k=60

**Dedup pipeline:**
1. URL normalization (lowercase, strip params, trailing slash)
2. Higher RRF score wins
3. Tie → source weight (Hagstofa > Alþingi > Vísindavefur > Mojeek)
4. Tie enn → first-seen (deterministic)

---

## 6. `<think>` Strip Implementation (D6)

**Primary regex:**
```python
import re
def strip_think_tags(raw: str) -> tuple[str, str]:
    think_match = re.search(r'<think>(.*?)</think>', raw, flags=re.DOTALL)
    think_content = think_match.group(1) if think_match else ""
    # Edge case: unclosed tag → strip from <think> til EOF
    clean = re.sub(r'<think>.*?</think>', '', raw, count=1, flags=re.DOTALL)
    clean = re.sub(r'<think>.*$', '', clean, flags=re.DOTALL)
    return clean.strip(), think_content
```

**Audit:** think_content skrifað í audit JSONL (aldrei í notendaviðmót)
**Edge cases:** Nested tags, inline mention, unclosed tag — allt covered
**Test cases í Phase F:** covered í eval regression

---

## 7. Phase D-G Ordering

| Phase | Verk | Deliverable | Acceptance criteria |
|-------|------|-------------|---------------------|
| D | Hagstofa hybrid | hagstofa_source.py | Mannfjöldi Q1 2026 í svar |
| D+1 | `<think>` patch | agent_core_v4.py | Engin think tags í notendaviðmót |
| E | Routing redesign | agent_core_v4.py | Íslensk query → Tier 2 first |
| F | Eval regression | eval_results.json | sovereignty_share baseline skráð |
| G | Tag | git tag | v87-routing-rc1 pushed |

---

## 8. Risk Register

| Risk | Líkur | Áhrif | Mótráðstöfun |
|------|-------|-------|--------------|
| Hagstofa rate limit | Meðal | Há | 1 req/s + 24h cache |
| Embedding cost 1,706 töflur | Lág | Meðal | One-time batch, ekki endurtekið |
| Baseline regression í routing | Meðal | Há | Phase F eval áður en tag |
| Dedup false positive (sama efni, mismunandi URL) | Lág | Lág | URL norm + manual spot-check |
| `<think>` edge cases í streaming | Meðal | Meðal | Defensive regex + audit log |

---

**STATUS:** Tilbúið fyrir Opus review → Phase D implementation
## 2. Source Registry Design (D2) — UPPFÆRT

**Skrá:** `config/source_registry.json`
**Validation:** Pydantic við server startup — fail-fast
**Hot-reload:** Restart-required í V1

```json
{
  "sources": [
    {
      "id": "althingi",
      "tier": 2,
      "tier_access": "both",
      "weight": 0.7,
      "access_pattern": "xml_api",
      "base_url": "https://www.althingi.is/altext/xml/",
      "rate_limit_rps": 1,
      "cache_ttl_hours": 24,
      "license": "public_domain",
      "attribution": "Alþingi Íslands"
    },
    {
      "id": "hagstofa",
      "tier": 2,
      "tier_access": "both",
      "weight": 0.7,
      "access_pattern": "hybrid_qdrant_dynamic",
      "base_url": "https://px.hagstofa.is",
      "rate_limit_rps": 1,
      "cache_ttl_hours": 24,
      "license": "CC_BY_4.0",
      "attribution": "Hagstofa Íslands"
    },
    {
      "id": "visindavefur",
      "tier": 2,
      "tier_access": "both",
      "weight": 0.7,
      "access_pattern": "html_search",
      "base_url": "https://www.visindavefur.is/search.php",
      "rate_limit_rps": 1,
      "cache_ttl_hours": 24,
      "license": "unknown",
      "attribution": "Vísindavefur Háskóla Íslands"
    },
    {
      "id": "stjornarradid",
      "tier": 2,
      "tier_access": "both",
      "weight": 0.7,
      "access_pattern": "html_search",
      "base_url": "https://www.government.is",
      "rate_limit_rps": 1,
      "cache_ttl_hours": 24,
      "license": "public_domain",
      "attribution": "Stjórnarráð Íslands"
    },
    {
      "id": "stjornartidindi",
      "tier": 2,
      "tier_access": "both",
      "weight": 0.7,
      "access_pattern": "html_search",
      "base_url": "https://www.stjornartidindi.is",
      "rate_limit_rps": 1,
      "cache_ttl_hours": 24,
      "license": "public_domain",
      "attribution": "Stjórnartíðindi"
    },
    {
      "id": "mojeek",
      "tier": 3,
      "tier_access": "vitinn",
      "weight": 0.3,
      "access_pattern": "rest_api",
      "base_url": "https://www.mojeek.com/search",
      "rate_limit_rps": 2,
      "cache_ttl_hours": 6,
      "license": "commercial",
      "attribution": "Mojeek",
      "sovereign": false
    }
  ]
}
```

---

## 3. Routing Redesign (D3 + D4) 

**Citation format:**
```json
{
  "source": "hagstofa",
  "table_id": "VIS01000",
  "title": "Vísitala neysluverðs",
  "accessed_at": "2026-05-17T08:14:00Z",
  "url": "https://px.hagstofa.is/pxis/api/v1/is/Efnahagur/visitolur/VIS01000",
  "sovereign": true
}
```

---

## 7. Phase D-G Ordering — UPPFÆRT

| Phase | Verk | Deliverable | Acceptance criteria | Tími |
|-------|------|-------------|---------------------|------|
| D | Hagstofa hybrid | hagstofa_source.py | Mannfjöldi Q1 2026 í svar með citation | 1-1.5d |
| D+1 | `<think>` patch | agent_core_v4.py | Engin think tags í notendaviðmót | 2-4 klst |
| E | Routing redesign | agent_core_v4.py | Íslensk query → Tier 2 first, vault Mojeek-free | 1d |
| F | Eval regression | eval_results.json | sovereignty_share baseline skráð, engin regression | ½d |
| G | Tag | git tag | v87-routing-rc1 pushed | ½d |
| **Heild** | | | | **3-4 dagar** |

