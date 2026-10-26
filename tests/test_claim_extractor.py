
import pytest

from services.claim_extractor import ClaimExtractor


@pytest.fixture
def extractor():
    """Create a ClaimExtractor instance for the tests."""
    return ClaimExtractor()


def test_extract_claim_removes_introductory_phrase(extractor):
    text = (
        "Breaking news: The government has banned "
        "UPI payments from tomorrow. Is this true?"
    )

    result = extractor.extract_claim(text)

    assert result == (
        "The government has banned UPI payments from tomorrow."
    )


def test_extract_claim_removes_extra_whitespace(extractor):
    text = "   The government   passed a new law today.   "

    result = extractor.extract_claim(text)

    assert result == "The government passed a new law today."


def test_extract_claim_rejects_empty_input(extractor):
    with pytest.raises(ValueError):
        extractor.extract_claim("   ")


def test_extract_claim_rejects_non_string_input(extractor):
    with pytest.raises(TypeError):
        extractor.extract_claim(123)


def test_extract_claim_rejects_short_input(extractor):
    with pytest.raises(ValueError):
        extractor.extract_claim("Not true")
