"""Sprint 68 B.1 — tests for LegalReference canonical schema."""
import pytest
from core.schemas import LegalReference


def test_document_level_fasteignalan():
    ref = LegalReference(
        law_nr=118, law_year=2016,
        law_title="um fasteignalán til neytenda",
        reference_type="document",
        raw_form="Lög um fasteignalán til neytenda nr. 118/2016",
    )
    assert ref.law_nr == 118
    assert ref.source_jurisdiction == "IS"


def test_internal_pinpoint_sigvaldi_example():
    """3. tl. 2. mgr. 36. gr. laga nr. 118/2016 — frá Sigvaldi."""
    ref = LegalReference(
        law_nr=118, law_year=2016,
        grein=36, malsgrein=2, tolulidur=3,
        reference_type="internal_pinpoint",
        raw_form="3. tl. 2. mgr. 36. gr. laga nr. 118/2016",
    )
    out = ref.to_canonical_string()
    assert "36. gr." in out
    assert "2. mgr." in out
    assert "3. tölul." in out


def test_external_requires_law():
    with pytest.raises(ValueError, match="law_nr"):
        LegalReference(
            grein=19,
            reference_type="external_pinpoint",
            raw_form="19. gr. laga nr. 79/2008",
        )


def test_grein_range_valid():
    ref = LegalReference(
        grein=10, grein_range_end=16,
        reference_type="grein_range",
        raw_form="10.–16. gr.",
    )
    assert "10.–16. gr." in ref.to_canonical_string()


def test_grein_range_invalid_order():
    with pytest.raises(ValueError, match="greater"):
        LegalReference(
            grein=16, grein_range_end=10,
            reference_type="grein_range",
            raw_form="16.–10. gr.",
        )


def test_kafli_roman_normalization():
    ref = LegalReference(
        kafli_roman="IX",
        grein=43,
        reference_type="internal_pinpoint",
        raw_form="43. gr. IX. kafla",
    )
    assert ref.kafli_int == 9


def test_grein_suffix_amended_article():
    """51. gr. a — amended article, empirical finding from 118/2016."""
    ref = LegalReference(
        law_nr=118, law_year=2016,
        grein=51, grein_suffix="a",
        reference_type="internal_pinpoint",
        raw_form="51. gr. a",
    )
    out = ref.to_canonical_string()
    assert "51. gr. a" in out
    assert "118/2016" in out
