# Sprint 68 Track C.0 — HTML Pattern Discovery

## Empirical basis
Snapshot 157a (2026-04-24), 3 lög, 828 KB HTML total:
- 1994145_bokhald.html (119 KB)
- 2016118_fasteignalan.html (183 KB)
- 2018090_personuvernd.html (526 KB)

## Findings

### 1. Amended articles are REAL (Opus was right)
| Law | X. gr. a occurrences | Examples |
|---|---|---|
| Bókhald (145/1994) | 0 | — |
| Fasteignalán (118/2016) | 12 | 51. gr. a, 51. gr. b, 16. gr. a, 58. gr. a |
| Persónuvernd (90/2018) | 0 | — |

**Decision**: Schema v0.4 adds `grein_suffix: Optional[str]`.

### 2. tölul. (full) dominates tl. (short): 41 vs 0
Alþingi never uses `tl.` in raw HTML. Canonical output = `tölul.`.
Chunker parser accepts both forms as input.

### 3. laga nr. (full) dominates l. (short): 2 vs 0
Canonical output = `laga nr.`.

### 4. Anchor IDs: ZERO
Eplica CMS does not emit `<a name="G14">` anchors.
Chunker must use text-based structural markers, not DOM anchors.

### 5. CSS classes are TOC nav, not structural
Top classes (`branch`, `level3`, `last`) are navigation, not grein/mgr markers.
Chunker strips HTML and works on plain text with regex.

### 6. Editorial markers consistent across all 3 laws
Strip list: `Lagasafn`, `útgáfa`, `Prenta í`, `tveimur dálkum`.

### 7. No tables in samples (skattalög pending)
Table handling deferred until 90/2003 (tekjuskattur) is added to samples.

## Structural marker counts
| Law | Grein | Kafli | Málsgrein | Amended |
|---|---|---|---|---|
| 145/1994 | 144 | 6 | 18 | 0 |
| 118/2016 | 246 | 33 | 86 | 12 |
| 90/2018 | 645 | 47 | 384 | 0 |

## Chunking strategy implications for C.1
- Strip HTML → plain text
- Regex-based parsing on structural markers
- Grein-level atomic unit (with málsgrein as secondary split)
- Chapter (kafli) is structural boundary, not pinpoint
- Citation output: Alþingis-canonical forms (tölul., laga nr.)
- Input parsing: accept both short (tl., l.) and full forms
