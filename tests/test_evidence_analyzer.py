
import pytest

from services.evidence_analyzer import EvidenceAnalyzer


@pytest.fixture
def analyzer():
    """Create an analyzer instance for each test."""
    return EvidenceAnalyzer()


def test_analyze_source_detects_relevant_keywords(analyzer):
    claim = "The government banned UPI payments from tomorrow."

    source = {
        "title": "UPI Payment Update",
        "url": "https://example.com/news",
        "text": (
            "The government announced new UPI payment rules. "
            "Banks will implement the updated payment rules tomorrow."
        ),
    }

    result = analyzer.analyze_source(claim, source)

    assert result["overlap_score"] > 0
    assert result["matched_keywords"]
    assert result["stance"] == "needs_review"


def test_analyze_source_flags_contradiction_marker(analyzer):
    claim = "The government banned UPI payments."

    source = {
        "title": "UPI Claim Fact Check",
        "url": "https://example.com/fact-check",
        "text": (
            "The claim that the government banned UPI payments "
            "is false. No such ban was announced."
        ),
    }

    result = analyzer.analyze_source(claim, source)

    assert result["stance"] == "potential_contradiction"
    assert result["overlap_score"] > 0


def test_analyze_source_marks_unrelated_content(analyzer):
    claim = "The government banned UPI payments tomorrow."

    source = {
        "title": "Weather Report",
        "url": "https://example.com/weather",
        "text": (
            "The weather forecast predicts rainfall and cloudy skies "
            "across the region throughout the coming week."
        ),
    }

    result = analyzer.analyze_source(claim, source)

    assert result["stance"] == "unrelated"
    assert result["overlap_score"] < 0.20


def test_analyze_source_handles_missing_text(analyzer):
    source = {
        "title": "Empty Article",
        "url": "https://example.com/empty",
        "text": "",
    }

    result = analyzer.analyze_source(
        "The government announced a new policy today.",
        source,
    )

    assert result["stance"] == "insufficient_information"
    assert result["relevant_sentences"] == []
    assert result["overlap_score"] == 0.0


def test_analyze_source_rejects_empty_claim(analyzer):
    with pytest.raises(ValueError):
        analyzer.analyze_source(
            "",
            {"text": "Some source text"},
        )


def test_analyze_source_rejects_invalid_source(analyzer):
    with pytest.raises(TypeError):
        analyzer.analyze_source(
            "The government announced a new policy today.",
            "not a dictionary",
        )


def test_analyze_source_rejects_non_string_text(analyzer):
    with pytest.raises(TypeError):
        analyzer.analyze_source(
            "The government announced a new policy today.",
            {"text": 123},
        )


def test_analyze_multiple_sources(analyzer):
    claim = "The government announced new UPI payment rules."

    sources = [
        {
            "title": "Source One",
            "url": "https://example.com/one",
            "text": (
                "The government announced new UPI payment rules "
                "that banks will implement next month."
            ),
        },
        {
            "title": "Source Two",
            "url": "https://example.org/two",
            "text": "",
        },
    ]

    results = analyzer.analyze(claim, sources)

    assert len(results) == 2
    assert results[0]["title"] == "Source One"
    assert results[1]["stance"] == "insufficient_information"


def test_analyze_rejects_non_list_sources(analyzer):
    with pytest.raises(TypeError):
        analyzer.analyze(
            "The government announced a new policy today.",
            "not a list",
        )
