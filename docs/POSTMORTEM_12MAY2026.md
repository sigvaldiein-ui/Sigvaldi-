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

## Lærdómur #90 (nýr 12. maí 2026)

**Vault tier framleiðir confident hallucinations án rauntímaleitar.**
Staðfest 22:35: Hvelfingin svaraði „Jón Davíð Halldórsson" fyrir
forsætisráðherra — algjör uppspuni, af fullkomnu öryggi.
Orsök: Vault (`tier=vault`) fer beint á Qwen vLLM án
`_get_search_context`. Engin leit, engar heimildir, engin vörn.
P0 fix á morgun: tengja rauntímaleit við Hvelfinguna.

## Sprint 81 Lessons (13.-14. maí 2026)

### Lesson #91 — Lykkjubani
while true án port cleanup eykur kerfisálag og veldur 
endurteknum Errno 98 villum. Lausn: smart restart pattern
með pkill á viðkomandi port áður en endurræst.

### Lesson #92 — Python re import
ast.parse staðfestir syntax en grípur ekki runtime NameError. 
Þegar middleware er uppfært og nýtt import er kallað á, verður 
að flytja `import re` (og önnur runtime dependencies) að toppi 
módúlsins. Combined með Lesson #86: ÞARF RUNTIME SMOKE TEST 
ofan á AST gate.

### Lesson #93 — Nýtt terminal bjargar
Þegar aðalskel frýs við cascading pkill operations, opnar 
Sigvaldi nýtt terminal og keyrir cleanup þaðan. Operational 
pattern fyrir RunPod environment.

### Lesson #94 — PATH handling í ræsiskriftum
nohup hefur minimal PATH. Ræsiskriftur verða að setja PATH og PYTHONPATH 
sjálfar, og nota fulla slóð á python3. start_alvitur.sh Exit 127 leyst.

### Lesson #95 — Token rotation discipline
CF Tunnel token getur orðið ógilt. Þarf að skrá rotation í viðhaldsáætlun
og hafa skjótan endurheimtingarferil. DNS record + nýtt token workflow staðfest.

### Lesson #96 — Cache isolation per tier
Skyndiminni verður að vera einangrað eftir tier (Vitinn / Hvelfing).
Sameiginlegt skyndiminni veldur því að vault-svör leka yfir í almennar
fyrirspurnir. Lausn: tvö aðskilin skyndiminni í YfirErindreka.

### Lesson #97 — Routing by content, not user flag
Routing rökfræði verður að byggja á innihaldi fyrirspurnar (PII Sentry,
domain, complexity), ekki bara `tier` frá notanda. Notandi getur valið
vault, en kerfið á líka að geta flokkað viðkvæmar fyrirspurnir sjálft.
