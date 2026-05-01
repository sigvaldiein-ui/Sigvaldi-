# Sprint 68 C.1 — Chunker Strategy Design
# Dagsetning: 24. april 2026 | Sonnet 4.6
# Basis: 4 log, 1840 chunks, s68-c05

## 1. PRIMARY ATOMIC UNIT
Hvert chunk = ein grein. Malsgrein = sub-chunk med parent_chunk_id.
Threshold sub-split: token_count > 400.
Empirical (4 log):
- 145/1994: 2/86 yfir 400 (2.3pct)
- 90/2003:  7/1027 (0.7pct)
- 118/2016: 4/185 (2.2pct)
- 90/2018:  12/542 (2.2pct)
- Samtals:  25/1840 (1.4pct) thurfa sub-split

## 2. CHUNK PAYLOAD SCHEMA
chunk_id:        str  # 145_1994_g14 / 145_1994_g14_m2
law_nr:          int
law_year:        int
law_title:       str
kafli_roman:     str|None
kafli_int:       int|None
grein:           int
grein_suffix:    str|None   # a, b, l, s
malsgrein:       int|None
text:            str
token_count:     int
chunk_level:     str        # grein | malsgrein
parent_chunk_id: str|None
related_refs:    list       # List[LegalReference]
source_url:      str
snapshot_version: str       # 157a
snapshot_date:   str        # 2026-04-24

Qdrant indexed fields: chunk_id, law_nr, law_year, kafli_int, grein, chunk_level, token_count
related_refs: JSON payload, ekki indexed.

## 3. HTML PARSING — ORDER OF OPERATIONS
1. LOAD html skra
2. STRIP HTML TAGS:   re.sub("<[^>]+>", " ", raw)
3. STRIP EDITORIAL:   Lagasafn, utgafa, Prenta i, tveimur dalkum, Athugid
4. PARSE KAFLAR:      finna kafla boundaries, tag hvern kafla
5. PARSE GREINAR:     splitta a grein markers, assign kafla
6. EXTRACT REFS:      INLINE_REF_PAT yfir hvern chunk
7. SUB-SPLIT:         ef token_count > 400, splitta a mgr markers
8. SERIALIZE:         chunk dicts -> JSONL

REGEX:
GREIN:  (\d+)\.\s*gr\.(?:\s+([a-z]{1,2}))?
MGR:    (\d+)\.\s*mgr\.
KAFLI:  (I{1,3}V?|IV|V?I{0,3}|IX|X{1,3})\.\s*kafl[ia]
REF:    (\d+)\.\s*(?:tl|tolul)\.\s*(?:(\d+)\.\s*mgr\.\s*)?(\d+)\.\s*gr\.(?:\s+([a-z]{1,2}))?(?:\s+(?:laga\s+nr\.|l\.?)\s*(\d+)/(\d{4}))?

## 4. EDITORIAL STRIP LIST
Lagasafn, utgafa N, Prenta i tveimur dalkum, Athugid..., [Breytt med...]
Preserve: structural markers, footnote text, hyperlink text (stripped af a tags)

## 5. INLINE REF EXTRACTION
Core feature. related_refs populatad fyrir hvert chunk.
grein_suffix (a,b,l,s) parsad baedi i chunk sjolfum og i related_refs.

## 6. CHUNK SIZE FORECAST
| Log        | Chunks | Median | p95 | >400tok |
| 145/1994   | 86     | 41     | 171 | 2       |
| 90/2003    | 1027   | 24     | 184 | 7       |
| 118/2016   | 185    | 33     | 281 | 4       |
| 90/2018    | 542    | 44     | 270 | 12      |
| Samtals    | 1840   | ~35    | ~227| 25      |

Medaltal chunks a log: 460
Full lagasafn ~1000 log: ~460,000 chunks
Med sub-chunks: ~480,000 Qdrant vectors
Vel innan Qdrant free tier (1M).

## 7. VALIDATION PLAN
C.2 Unit tests:
- test_parse_bokhald_chunk_count() -> 80 < n < 100
- test_chunk_payload_fields() -> oll required fields til
- test_grein_suffix_parsed() -> suffix in [a,b,l,s] > 0
- test_sub_split_threshold() -> >400tok -> chunk_level==malsgrein
- test_editorial_stripped() -> Lagasafn ekki i texta

C.3 Integration tests:
- test_round_trip_identity() -> parse->JSONL->reparse->identity
- test_citation_round_trip() -> LegalReference->to_canonical_string()->exact match
- test_related_refs_populated() -> 90/2018 chunks med refs > 0
- test_nested_stafl_tolul() -> 90/2003 nested refs i related_refs

## 8. OPEN QUESTIONS FYRIR OPUS

Q1: grein_suffix l og s — merkingarlegt inntak othekkd.
    Baeta vid grein_suffix_type field i schema, eda leysa seinna?

Q2: kafli assignment fyrir greinar a undan fyrsta kafla marker.
    Tillaga: kafli_roman=None, kafli_int=0 sem pre-chapter sentinel.

Q3: related_refs scope — extracta allar refs eda bara external?
    Tillaga: allar, merkja reference_type, filtrun seinna.

Q4: token_count method — whitespace-split eda tiktoken BPE?
    Tillaga: tiktoken cl100k_base fyrir embedding accuracy.
