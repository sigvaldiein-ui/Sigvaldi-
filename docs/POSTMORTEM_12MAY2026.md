# Postmortem — 12. maí 2026

## Tímalína atburða

| Tími | Atburður |
|------|----------|
| ~08:00 | Byrjuð vinna við að opna Hvelfinguna og laga flipa |
| ~10:00 | Heimildagátt aftengd af Leið A, Honest Data Gap bætt við |
| ~13:00 | Tilkynnt um empirical árangur sem ekki hafði verið sannreyndur |
| ~14:00 | Stem-matching breyting á stjornarradid_source.py olli regressioni |
| ~15:00 | Önnur tilkynning um árangur án sannreyningar |
| ~16:00 | Full git rollback til v80c-v2-rc1 — Kristrún Frostadóttir endurheimt |
| ~18:00 | Opus skipaði stöðvun allra kóðabreytinga |

## Rótarvandamál

### 1. Ósannreyndar fullyrðingar um árangur
Per tilkynnti tvisvar að breytingar hefðu skilað réttum niðurstöðum án þess að Sigvaldi hefði keyrt prófanir.
**Lærdómur #60 brotinn.**

### 2. Stem-matching refactoring olli afturför
**Lærdómur #89 (nýr):** Stem-matching var ekki lagfæring — það var afturför.

### 3. Uppsöfnuð þreyta eftir 30+ klst vinnu

## Lærdómar

| # | Lærdómur |
|---|----------|
| 60 | Aldrei segja verk „lokið" án empirical verification |
| 78 | Engin Python strengja-parsing í bash heredoc |
| 86 | Nota sérstakar exceptions í stað broad try/except |
| 87 | Temperature 0.0 + HEIMILDIR merkingar = strong RAG anchoring |
| 88 | LLM svarar án empirical stuðnings skáldar trúverðugar staðreyndir |
| 89 | Stem-matching á stjornarradid_source.py var regression, ekki fix |

## Úrbætur

- Strict empirical protocol: Per skrifar skipanir, Sigvaldi keyrir.
- Engin self-GREEN.
- Skyldubundin hlé eftir 3 klst.
- Full file replacement í stað partial diff.

## Núverandi staða

- v80c-v2-rc1 er stable baseline
- Kristrún Frostadóttir svar virkar
- Heimildagátt er óvirk (source_gate.py er munaðarlaus skrá)
- Git tree er hreint (aðeins untracked skrár)
