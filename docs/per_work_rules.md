# Per (DeepSeek V5) Strict Work Rules

**Bindandi frá:** Sprint 75 (1. maí 2026)
**Tilefni:** Sprint 74 K3 endurkeyrsla.
**Valdsvið:** Opus enforcer, Per fylgir.

## Reglur

1. Engin inline Python í bash heredoc — allur kóði í .py skrá
2. Read-before-write — lesa existing áður en skrifað er nýtt
3. Empirical diagnosis fyrir workaround — root-cause fyrst
4. CLI args staðfestar áður en skipun keyrð
5. Checkpoint + idempotent insert fyrir >1000 records
6. NFC + íslensk regex — endurnota K2 chunker pattern
7. Aldrei snerta production án Opus GREEN
8. Eitt skref per bash blokk
9. Aldrei sjálf-GREEN — bíða eftir Opus staðfestingu
10. Max 2 iterations per gate — svo ping með specific ask

## Lessons úr Sprint 74
- #41: Inline heredoc Python brýtur öryggi og review
- #42: Re-implementation duplikerar bugs
- #43: Workaround án diagnose felur falinn bug
