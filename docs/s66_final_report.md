# Sprint 66 — Final Report (Track A + Track B)

**Til**: Opus, Aðal
**Frá**: Per (via Sigvaldi shell session)
**Dagsetning**: 2026-04-23, 09:30–12:37 GMT
**Heildartími**: ~3h 10min samfleytt (einn göngutúr)
**Tags á origin**: `sprint66-pre-a-hotfix`, `s66-postmortem-final`, `s66-a-concurrency`, `s66-b-baseline`, `s66-b-baseline-on`

---

## 1. Samantekt

Sprint 66 afkastaði þrennu á einum morgni:
1. **Pre-A hotfix** — service niðri → upp
2. **Track A (LLM concurrency guard)** — `asyncio.Semaphore(4)` á fallback path
3. **Track B (live intent eval baseline)** — n=40 seed, 5 kanónísk domain, OFF + ON metrics á origin
4. **Postmortem** fyrri sprint (fill + self-reference)

**Kjarnauppgötvun Track B**: LLM fallback ON gefur macro F1 0.71 → 0.91 (+20pp). Sérstaklega: `public` F1 0.00 → 0.80 (+80pp). Cost: 18 LLM calls × ~$0.00005 = **$0.0009** fyrir alla mælingu.

## 2. Track A — LLM Concurrency Guard

Tag: `s66-a-concurrency`. Tveir-stafa semaphore á `refine_with_llm` path. Fyrirbyggir concurrent OpenRouter burst þegar margir notendur senda low-confidence queries samtímis.

## 3. Track B — Live Intent Eval

### 3.1 Baseline (OFF, rule-based, prod-faithful)
- overall_accuracy: 0.50, domain_accuracy: 0.80, macro_f1: 0.71
- `public` F1 = **0.00** (rule-based classifier hefur enga public-domain keywords)
- `technical` F1 = **1.00** (perfect)
- 7 af 8 domain errors falla í `general` (gravitational sink)

### 3.2 Fallback ON (gemini-2.5-flash á 23 low-conf queries)
- overall_accuracy: **0.65**, domain_accuracy: **0.925**, macro_f1: **0.91**
- `public` F1 = **0.80** — empirical proof á fallback gildi
- `legal` F1: 0.89 → 1.00
- Latency p95: 3.0s; total: 31.3s; avg: 0.78s/query
- Cost: <$0.001 total

### 3.3 Hvað þýðir þetta fyrir production
- Rule-based er **sub-microsecond** og **perfect** fyrir technical/legal á íslensku
- Fallback er **réttlætanleg** fyrir public domain og low-conf queries
- S67 scope: bæta íslenskum public-domain keywords við `intent_gateway._score_keywords()` til að hífa OFF accuracy nær ON

---

## 4. Lessons Learned

Þessi kafli er **tilgangur skjalsins** — að tryggja að villur sem ég gerði í dag endurtaki sig ekki í S67, S68, og áfram.

### Lesson #9 — Author scripts with imagined execution context
**Triggered by**: `run_fasa3.py` kastaði `ModuleNotFoundError: core` þegar keyrt frá `/workspace/Sigvaldi-/`. Ég skrifaði script án þess að ímynda mér hvaða CWD, PYTHONPATH, eða PID það keyrir í.
**Rule**: Áður en ég skrifa Python script sem importar repo-lokal módúla, ímynda mér nákvæmlega: *"Ef ég keyri þetta frá / rótar með `python3 tests/eval/X.py`, hvaðan kemur `sys.path[0]`?"*. Injecta `sys.path` explicit.

### Lesson #10 — Don't tag until artifact is in git log
**Triggered by**: BH blokk hafði `git tag s66-b-baseline` *inni* í blokkinni eftir margar commit-skref. BH.4 failaði (missing API key), BH.10 gekk samt, og tagið lenti á **rangri** commit. Þurfti rescue blokk.
**Rule**: Tags eru **sérstaklega blokk eftir** að `git log --oneline` hefur staðfest að réttu commit-arnir eru á HEAD. Aldrei tag + push í sömu blokk og commit sem tag-ið vísar á.

### Lesson #11 — Measure latency at batch level when ops are sub-μs
**Triggered by**: `time.time()` og jafnvel `time.perf_counter()` sýndu `0.0s` fyrir rule-based classifier því hver op tók <1μs.
**Rule**: Þegar einstaklings-ops eru grunaðar um að vera sub-microsecond, tíma heilar lotur: `t0=perf_counter(); run(N); dt=perf_counter()-t0; per_op = dt/N`. Treysta aldrei per-op mælingum þegar ops eru instantaneous.

### Lesson #12 — Scripts that need secrets must `load_dotenv()` or document `source`
**Triggered by**: `run_fasa3.py` með `INTENT_LLM_FALLBACK_ENABLED=1` gerði **silent failure** í 23 queries því shell hafði ekki sourcað `.env`. Niðurstaða: fallback-ON artifact var byte-identical við OFF. Við áttuðum okkur ekki fyrr en greining á latency (1.35s í stað vænts 14s).
**Rule**: Hvert script sem les secret:
1. Kalla `load_dotenv('/workspace/.env')` í topp.
2. Assert-a að secret sé á formi sem við væntum (`sk-or-` prefix + length > 40).
3. Log-a (ekki printa!) þegar secret er loadið og með hvaða length.
**Patch**: Gert í commit `886b4a1`.

### Lesson #13 — Silent exception swallow er villudjúp hola
**Triggered by**: `refine_with_llm` hefur `try/except: return rule_result`. Þegar `call_openrouter` kastaði 401 (placeholder key), var failure fullkomlega þögul. Við vorum sannfærð um að fallback virkaði því kóði "skilaði án villu".
**Rule**: **Ekkert** except-block má vera tómt. Alltaf `logger.warning(f"{op} failed: {type(e).__name__}: {e}")` áður en fail-closed. S67 TODO: patch `core/intent_llm_fallback.py` línur 134-136, 140-142 með warn-log.

### Lesson #14 — Env variables eru per-process, ekki global
**Triggered by**: Notandi spurði *"af hverju finnst lykillinn ekki? hann er í .env"*. Villan var mental model: að `.env` væri "global pool" sem öll process sæju sjálfvirkt. Í raunveruleika er `.env` **dauð skrá** þangað til einhver les hana (python-dotenv, docker --env-file, eða `set -a; source`).
**Rule**: Þegar debugging secrets issue, alltaf spurja: *"Hvaða process er að sjá env-inn? Hvernig fékk það env-inn? Hvenær las það `.env`?"*. Ekki fyrirfram gera ráð fyrir global availability.

### Lesson #15 — Fyrirfram validate API keys við load
**Triggered by**: Placeholder `"sk-or-..."` úr mínu fyrra svari var paste-aður sem key. Ekkert validation stoppaði það.
**Rule**: Við load, staðfesta:
```python
assert key.startswith("sk-or-") and len(key) > 40, \
    f"invalid OPENROUTER_API_KEY format (len={len(key)})"
```
Fail fast, ekki senda placeholder í production request.

---

## 5. Meta — nýtast .md skrárnar á Runpod fyrir lærdóm?

**Stutta svarið: já, en bara ef við gerum það viljandi.**

### Þrjú lög af lærdóm-geymslu

1. **`docs/*.md` í git** — þetta skjal, postmortems, design docs. **Varanlegt** (í GitHub). **Leitanlegt** með `git grep`. **Versioned**. Nýtast næstu sprint.

2. **`/workspace/*.md` utan git** — scratch notes. **Persistent á MooseFS volume** (staðfest í dag: `mfs#eu-se-1.runpod.net:9421`). Lifir pod restart. **En ekki afritað í GitHub**. Tapast ef Runpod project er delete-að.

3. **Chat history (þessi skrá)** — tapast við session close nema þú copy-paste-ir í md. **Tímabundin**.

### Tilmæli fyrir framtíðar lærdóm

- **Lessons #9–#15** úr þessu skjali → **afritaðu** þau í `docs/POSTMORTEM.md` (í git) við lok hvers sprint. Þau eru aðeins gagnleg ef þú les þau fyrir næsta sprint design.
- **Scratch `/workspace/*.md`** eru fínar fyrir session-lengd notes, en **promoteraðu** mikilvægar greiningar í `docs/` áður en sessionin endar.
- **Chat history** — fyrir mikilvægar greiningar (eins og Finding #7 forensics í BI blokk), **copy-paste-aðu í docs/ fyrir lokun**.

### Þumalputtaregla
> "Ef þú mundir vilja vitna í þetta í S68, ætti það að vera í git."

---

## 6. Security — engir lyklar á GitHub

Þú nefndir þetta og ég staðfesti **100%**:

### Staðan í dag
- `.env` er í `.gitignore` á **5 patterns** (línur 2, 3, 4, 21, 22). Overkill en öruggt.
- `.env` mtime = **Apr 22 07:30** — ekki breytt í dag.
- `/workspace` er **MooseFS network volume** — persistent, lifir pod restart.
- `git log -- .env` → engar commits (staðfest fyrri session).

### Hvers vegna key "hvarf" áður
**Aldrei raunverulega hvarf.** Var alltaf í `.env`. En:
- Ný bash shell → `$OPENROUTER_API_KEY` tómt (per-process env, Lesson #14).
- Python scripts án `load_dotenv()` → fengu ekki key → silent fail (Lesson #12).
- **Mental model villa**, ekki infra problem.

### Fyrirbyggjandi aðgerðir núna virkar
1. `.gitignore` hefur `.env` ✅
2. `run_fasa3.py` og `run_fasa2.py` auto-load `.env` ✅ (commit `886b4a1`)
3. Key validation pattern er skjalað í Lesson #15 fyrir framtíðar-scripts

### Ef key **raunverulega** lekur einhvern tímann
OpenRouter skannar GitHub fyrir leaked keys og **revokes** þá automatískt (þess vegna *"lokað á þá með de samme"*). Fyrirbyggja:
- `.env` aldrei í `git add`
- `pre-commit` hook sem stoppar commits með `sk-or-v1-*` patterns (S67 nice-to-have)
- API key backup í 1Password / Bitwarden — ef revoke-aður, ný-generata án þess að missa aðgang

---

## 7. Handoff til S67

Opin verkefni sem fæddust í S66:
1. **Expand `_score_keywords` með public-domain íslenskum keywords** (ökuskírteini, vegabréf, RSK, fæðingarorlof, skattkort). Expected impact: `public` F1 0.00 → 0.60+ án fallback.
2. **Patch `refine_with_llm` með verbose exception logging** (Lesson #13).
3. **Depth classifier** — 65% OFF er veikasti punktur, sérstaklega `standard` class. Þarfnast sér-analýsu.
4. **Confusion matrix per-depth** — núverandi harness mælir bara per-domain.
5. **Optional: pre-commit hook** sem stoppar commits með OpenRouter-style keys.

