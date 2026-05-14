# Sprint 80c v3 — Vault Search Integration

## Empirical Evidence

22:35 12. maí 2026: Hvelfingin (Vault/Vault tier) svarar
"Hver er forsætisráðherra Íslands?" með „Jón Davíð Halldórsson" —
algjör uppspuni, af fullkomnu öryggi.

Orsök staðfest: Vault tier (`tier=vault`) fer beint á Qwen vLLM án
`_get_search_context`. Engin leit, engar heimildir, engin vörn.

## Scope

Tengja `_get_search_context` við Vault tier í `chat_routes.py`,
líkt og þegar er gert fyrir Leið A. Vault fær sömu leitarniðurstöður
(Mojeek, Stjórnarráð, Stjórnartíðindi, Wayback) en með strangara
prompti og heimildavörnum.

## Guardrail: Fail-Secure PII Filter

Áður en Vault sendir leitarfyrirspurn á ytri þjónustur (Mojeek/CDX),
skal `_strip_pii_for_search` fjarlægja kennitölur.
Ef `VAULT_STRICT_NO_EXTERNAL=true` (sjálfgefið) og PII finnst,
sleppir Vault ytri leit og notar aðeins RAG (núverandi hegðun).

## Tími

2 klst í fyrramálið (14. maí 2026).

## Acceptance Criteria

- Hvelfingin svarar „Hver er forsætisráðherra Íslands?" með
  réttu nafni (Kristrún Frostadóttir) eða heiðarlegri neitun,
  ekki uppspuna.
- Sama fyrir fjármálaráðherra, dómsmálaráðherra, heilbrigðisráðherra.
- PII próf: fyrirspurn með kennitölu fer EKKI út í ytri leit.
- Leið A (Vitinn) verður fyrir engri röskun — Kristrún svar
  virkar áfram.
