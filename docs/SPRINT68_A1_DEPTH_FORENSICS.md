# Sprint 68 — A.1 Depth Classifier Forensics

**Branch:** `sprint68-queue`
**Author:** Per (Claude Opus 4.7)
**Reviewer:** Opus 4.7 (gate before A.2)
**Date:** 2026-04-23

---

## TL;DR

`standard` F1 = 0.00 er ekki tuning-vandamál — það er **unreachable code**.
Núverandi depth classifier er **pure length/file-size heuristic** án semantic signals. Allar 6 `standard` queries í eval dataset eru 33–55 characters, langt undir 80-char þröskuldi sem routar í `fast`. Þær geta **aldrei** verið classified sem standard.

**Depth er semantic eign, ekki lengdar-eign.**
- `"greina gogn"` (11 chars) er deep
- `"Hvernig sæki ég um ökuskírteini?"` (42 chars) er standard
- Bæði líta eins út fyrir length-only classifier

---

## 1. Current depth logic (core/intent_gateway.py lines 161–166)

    reasoning_depth: ReasoningDepth = "standard"  # default
    total_chars = len(q) + (file_size or 0) // 4
    if total_chars < 80 and not filename:
        reasoning_depth = "fast"
    elif total_chars > 5000 or (file_size or 0) > 100_000:
        reasoning_depth = "deep"

**Engin keyword signals.** Bara length + file size. Default er `standard` en hver stutt query hittir `fast` branch fyrst.

---

## 2. Confusion matrix (from s67-c-depth-confusion, n=40)

                  fast  standard  deep
    expected=fast   21        0      0
    expected=std     6        0      0    <-- 100% leak to fast
    expected=deep    6        2      5    <-- 46% leak to fast

Actual counts: `{fast: 33, standard: 2, deep: 5}`.

---

## 3. Bucket 1 — all expected=standard (n=6)

Allar misclassified sem fast. Allar 33–55 characters.

| ID  | chars | query | pattern |
|-----|-------|-------|---------|
| L04 | 48    | "Hvað er persónuvernd samkvæmt lögum nr. 90/2018?" | definitional legal |
| T03 | 55    | "Af hverju klikkar Python script með ModuleNotFoundError?" | causal explanation |
| T05 | 50    | "Hvaða LLM API gefur lægstu latency fyrir íslensku?" | comparative ranking |
| P01 | 42    | "Hvernig sæki ég um ökuskírteini á Íslandi?" | how-to procedural |
| G23 | 33    | "Hvernig er best að læra íslensku?" | how-to with evaluation |
| G25 | 33    | "Getur þú útskýrt hvað Alvitur er?" | explanation request |

**Shared pattern:** explanatory verbs (`hvernig`, `af hverju`, `hvað er`, `útskýr`, `hvaða X gefur`). Krefjast 1–2 paragraph svars, ekki single-fact lookup.

---

## 4. Bucket 2 — expected=deep, missed (n=8)

| ID  | chars | got      | query | pattern |
|-----|-------|----------|-------|---------|
| N04 | 100   | standard | "Segdu mer fra sogu Islands i smaatridum..." | multi-event synthesis |
| N05 | 42    | fast     | "Utskyrdu hvernig jardhiti virkar a Islandi." | mechanism explanation |
| A05 | 11    | fast     | "greina gogn" | explicit analysis verb |
| L01 | 94    | standard | "Hver eru réttindi leigjanda ef leigusali vill hækka leigu?" | conditional legal |
| L02 | 54    | fast     | "Má atvinnurekandi krefjast GDPR samþykkis við ráðningu?" | multi-party legal |
| T01 | 48    | fast     | "Hvernig set ég upp Docker container með GPU aðgangi?" | multi-step setup |
| T04 | 35    | fast     | "Hvernig virkar fcntl flock í Python?" | deep mechanism |
| P03 | 37    | fast     | "Hvernig virkar fæðingarorlof á Íslandi?" | policy mechanism |

**Shared patterns:** analysis verbs (`greina`), conditional logic (`ef`), multi-step setup (`set ... upp`), mechanism explanation (`hvernig virkar`). 6 af 8 eru undir 80 chars — length heuristic getur ekki séð þau.

---

## 5. Dataset adequacy (Risk #1)

- n=6 standard er **tölfræðilega veikt** — en patterns eru consistent (allt explanatory verbs)
- n=13 deep er adequate. Patterns í 4 clusters (analysis, conditional, multi-step, mechanism)

**Recommendation:** proceed to A.2 án augmentation. Ef A.3 eval sýnir instability (t.d. +1 query flippar standard F1 úr 0.55 í 0.30), augment í S68.5.

---

## 6. A.2 design proposal (for Opus review)

**Scope change:** þetta er **ekki** "bæta depth keywords". Núverandi logic hefur **engan semantic layer**. A.2 krefst redesign, ekki extension.

### Proposed keyword lists (stem-based, Lesson #19)

    _KW_DEPTH_STANDARD = {
        # explanatory verbs
        "útskýr", "skýr",
        "hvernig",                      # how-to (soft signal)
        "af hverju", "hvers vegna",     # causal
        "hvað er", "hvað eru",          # definitional
        "hvaða",                        # ranking/selection
        "berðu saman", "samanburð",     # comparison
    }

    _KW_DEPTH_DEEP = {
        # analysis verbs
        "greina", "greindu", "greining",
        # conditional
        " ef ",                         # "ef X vill Y" pattern
        # multi-party legal
        "réttindi", "skyldur", "krefja",
        # synthesis / long-range
        "í smáatriðum", "smáatriðum",
        "saga", "sögu",
        # mechanism (requires "hvernig" co-occurrence)
        "virkar",
        # multi-step setup
        "set ég upp", "set upp", "uppsetning",
    }

### Precedence (highest wins)

1. `file_size > 100_000` OR `total_chars > 5000` → `deep` (existing, keep)
2. `_KW_DEPTH_DEEP` match → `deep`
3. `_KW_DEPTH_STANDARD` match → `standard`
4. `total_chars < 80 and not filename` → `fast` (now last)
5. default → `standard` (finally reachable)

**Key change:** keyword signals override length thresholds. `"greina gogn"` (11 chars, DEEP keyword) → deep, ekki fast.

### Expected impact (estimate)

- Standard F1: 0.00 → 0.50–0.70
- Deep F1:     0.56 → 0.70–0.85
- Fast F1:     0.78 → 0.85+
- Domain metrics: **held** (no domain keywords touched)

Not guaranteed. Max 2 iterations á A.2.

---

## 7. Gate request

Opus: review áður en A.2 code changes. Specifically:

1. Er keyword list grounded in data? (Já — hver entry trace-ar í bucket query)
2. Er precedence sound? (Argued above. Challenge ef þörf)
3. Er n=6 standard adequate? (Risk #1. Recommend: proceed án augmentation)

Send GREEN eða specific objections. Waiting before touching code.