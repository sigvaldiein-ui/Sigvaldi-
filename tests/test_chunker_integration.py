"""Sprint 68 C.3 — Integration tests fyrir LegalDocumentChunker."""
import json, dataclasses
from core.ingestion.chunker import LegalDocumentChunker, Chunk
from core.schemas.legal_reference import LegalReference

LAWS = [
    ("data/bronze/logs/samples/1994145_bokhald.html",
     {"law_nr":145,"law_year":1994,"law_title":"um bokhald",
      "source_url":"https://www.althingi.is/lagas/nuna/1994145.html"}),
    ("data/bronze/logs/samples/2003090_tekjuskattur.html",
     {"law_nr":90,"law_year":2003,"law_title":"um tekjuskatt",
      "source_url":"https://www.althingi.is/lagas/nuna/2003090.html"}),
    ("data/bronze/logs/samples/2016118_fasteignalan.html",
     {"law_nr":118,"law_year":2016,"law_title":"um fasteignalan",
      "source_url":"https://www.althingi.is/lagas/nuna/2016118.html"}),
    ("data/bronze/logs/samples/2018090_personuvernd.html",
     {"law_nr":90,"law_year":2018,"law_title":"um personuvernd",
      "source_url":"https://www.althingi.is/lagas/nuna/2018090.html"}),
]

def _parse(path, meta):
    return LegalDocumentChunker().parse_html(open(path).read(), meta)

def test_chunk_count_all_laws():
    expected = {145: (60,200), 90: (400,1200), 118: (120,300)}
    for path, meta in LAWS:
        chunks = _parse(path, meta)
        n = len(chunks)
        nr = meta["law_nr"]; yr = meta["law_year"]; assert n > 20, f"{nr}/{yr}: of faar chunks ({n})"

def test_round_trip_identity():
    path, meta = LAWS[0]
    chunks = _parse(path, meta)
    for ch in chunks[:10]:
        d = dataclasses.asdict(ch)
        j = json.dumps(d, ensure_ascii=False)
        d2 = json.loads(j)
        assert d2["chunk_id"] == ch.chunk_id
        assert d2["text"] == ch.text
        assert d2["token_count"] == ch.token_count

def test_citation_round_trip():
    ref = LegalReference(
        law_nr=118, law_year=2016,
        grein=36, malsgrein=2, tolulidur=3,
        reference_type="internal_pinpoint",
        raw_form="3. tl. 2. mgr. 36. gr. laga nr. 118/2016",
    )
    out = ref.to_canonical_string()
    assert "36. gr." in out
    assert "2. mgr." in out
    assert "3. tolul." in out or "3. tölul." in out
    assert "118/2016" in out

def test_edge_cases_suffix_and_nested():
    path, meta = LAWS[2]  # 118/2016 - hefur a/b suffix
    chunks = _parse(path, meta)
    suffixed = [ch for ch in chunks if ch.grein_suffix is not None]
    assert len(suffixed) > 0, "Engin grein_suffix chunk fundin"
    # Nested: tekjuskattur hefur stafl+tolul
    path2, meta2 = LAWS[1]
    chunks2 = _parse(path2, meta2)
    nested = [ch for ch in chunks2 if len(ch.related_refs) > 0]
    assert len(nested) > 0, "Engar related_refs fundnar i 90/2003"

def test_ghost_chunk_regex_fix():
    """Stadfesta ad inline 14. gr. (innan setningar) er ekki chunk boundary."""
    c = LegalDocumentChunker()
    fake_html = """<p>14. gr.
Fyrsta grein laganna.
Sjá einnig 3. gr. og 7. gr. um nánari skilgreiningar.
</p>
<p>15. gr.
Onnur grein. Gildir um allt.
</p>"""
    meta = {"law_nr":999,"law_year":2026,"law_title":"prufulog","source_url":""}
    chunks = c.parse_html(fake_html, meta)
    grein_ids = [ch.grein for ch in chunks]
    # 14 og 15 skulu vera chunks, en inline 3 og 7 skulu EKKI
    assert 14 in grein_ids, "14. gr. (heading) parsast ekki"
    assert 15 in grein_ids, "15. gr. (heading) parsast ekki"
    inline_false = [ch for ch in chunks if ch.grein in (3, 7)]
    assert len(inline_false) == 0, f"Ghost chunks fundnir: {[ch.chunk_id for ch in inline_false]}"
