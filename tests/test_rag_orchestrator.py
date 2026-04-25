"""Sprint 70 Track C — Unit tests fyrir RAG+ orchestrator."""
import pytest
from unittest.mock import patch, MagicMock
from core.rag_orchestrator import retrieve_legal_context, build_rag_injection

def make_hit(score, chunk_id="118_2016_g20", level="grein"):
    h = MagicMock()
    h.score = score
    h.payload = {
        "chunk_id": chunk_id, "text": "Lagagrein texti.",
        "grein": 20, "grein_suffix": None, "malsgrein": None,
        "chunk_level": level, "parent_chunk_id": None,
        "law_nr": 118, "law_year": 2016,
        "law_title": "um fasteignalán til neytenda",
        "source_url": "https://www.althingi.is/lagas/nuna/2016118.html",
        "token_count": 225, "tenant_id": "system",
    }
    return h

def make_qr(hits):
    r = MagicMock(); r.points = hits; return r

def mock_qdrant_client(hits):
    """Helper - patcha QdrantClient i core.embeddings og core.rag_orchestrator."""
    mock = MagicMock()
    mock.return_value.query_points.return_value = make_qr(hits)
    return mock

def test_skip_retrieval_non_legal():
    result = retrieve_legal_context("hvað er klukkan", "general", "general")
    assert result.used_retrieval == False
    assert result.trigger_type == "none"

def test_primary_trigger_legal_domain():
    with patch("core.rag_orchestrator.embed", return_value=[0.1]*1024), \
         patch("core.rag_orchestrator.QdrantClient", mock_qdrant_client([make_hit(0.85)])):
        result = retrieve_legal_context("fasteignalán greiðslumat", "legal", "general")
    assert result.used_retrieval == True
    assert result.trigger_type == "primary"
    assert len(result.chunks) == 1

def test_secondary_trigger_keyword():
    with patch("core.rag_orchestrator.embed", return_value=[0.1]*1024), \
         patch("core.rag_orchestrator.QdrantClient", mock_qdrant_client([make_hit(0.75)])):
        result = retrieve_legal_context("hvað segir 36. gr. um þetta", "financial", "general")
    assert result.trigger_type == "secondary"
    assert result.used_retrieval == True

def test_vault_zero_hits_refusal():
    with patch("core.rag_orchestrator.embed", return_value=[0.1]*1024), \
         patch("core.rag_orchestrator.QdrantClient", mock_qdrant_client([])):
        result = retrieve_legal_context("lög um X", "legal", "vault")
    assert result.used_retrieval == False
    assert result.fallback_to_gemini == False
    assert result.refusal is not None

def test_general_zero_hits_fallback():
    with patch("core.rag_orchestrator.embed", return_value=[0.1]*1024), \
         patch("core.rag_orchestrator.QdrantClient", mock_qdrant_client([])):
        result = retrieve_legal_context("lög um X", "legal", "general")
    assert result.used_retrieval == False
    assert result.fallback_to_gemini == True
    assert result.refusal is None

def test_build_rag_injection_format():
    chunks = [{
        "chunk_id": "118_2016_g20", "text": "Lagagrein texti.",
        "grein": 20, "grein_suffix": None, "malsgrein": None,
        "law_nr": 118, "law_year": 2016,
        "law_title": "um fasteignalán til neytenda",
        "source_url": "https://althingi.is", "score": 0.85,
        "low_confidence": False, "parent_text": None,
    }]
    injection = build_rag_injection(chunks)
    assert "20. gr. laga nr. 118/2016" in injection
    assert "LEIÐBEININGAR" in injection

def test_low_confidence_flag():
    with patch("core.rag_orchestrator.embed", return_value=[0.1]*1024), \
         patch("core.rag_orchestrator.QdrantClient", mock_qdrant_client([make_hit(0.45)])):
        result = retrieve_legal_context("lög", "legal", "general")
    assert result.used_retrieval == True
    assert result.chunks[0]["low_confidence"] == True
