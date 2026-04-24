"""Sprint 68 C.2 — Unit tests fyrir LegalDocumentChunker."""
import pytest
from core.ingestion.chunker import LegalDocumentChunker

META_BOKHALD = {
    "law_nr": 145, "law_year": 1994,
    "law_title": "um bokhald",
    "source_url": "https://www.althingi.is/lagas/nuna/1994145.html"
}

def _html(path):
    return open(path).read()

def test_parse_bokhald_chunk_count():
    c = LegalDocumentChunker()
    chunks = c.parse_html(_html("data/bronze/logs/samples/1994145_bokhald.html"), META_BOKHALD)
    assert 80 < len(chunks) < 160

def test_chunk_payload_fields():
    c = LegalDocumentChunker()
    chunks = c.parse_html(_html("data/bronze/logs/samples/1994145_bokhald.html"), META_BOKHALD)
    required = ["chunk_id","law_nr","law_year","grein","text",
                "token_count","chunk_level","related_refs","source_url"]
    for ch in chunks[:5]:
        d = ch.__dict__
        for f in required:
            assert f in d, f"Missing field: {f}"

def test_grein_suffix_parsed():
    c = LegalDocumentChunker()
    meta = {"law_nr":118,"law_year":2016,"law_title":"um fasteignalan",
            "source_url":"https://www.althingi.is/lagas/nuna/2016118.html"}
    chunks = c.parse_html(_html("data/bronze/logs/samples/2016118_fasteignalan.html"), meta)
    suffixed = [ch for ch in chunks if ch.grein_suffix is not None]
    assert len(suffixed) > 0, "Engin grein_suffix fundin i 118/2016"

def test_sub_split_threshold():
    c = LegalDocumentChunker()
    meta = {"law_nr":90,"law_year":2003,"law_title":"um tekjuskatt",
            "source_url":"https://www.althingi.is/lagas/nuna/2003090.html"}
    chunks = c.parse_html(_html("data/bronze/logs/samples/2003090_tekjuskattur.html"), meta)
    sub = [ch for ch in chunks if ch.chunk_level == "malsgrein"]
    assert len(sub) > 0, "Engin malsgrein sub-chunks fundin"

def test_editorial_stripped():
    c = LegalDocumentChunker()
    chunks = c.parse_html(_html("data/bronze/logs/samples/1994145_bokhald.html"), META_BOKHALD)
    for ch in chunks:
        assert "Lagasafn" not in ch.text, f"Editorial marker i chunk {ch.chunk_id}"
