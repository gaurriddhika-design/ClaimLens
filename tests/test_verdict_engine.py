
import pytest

from services.verdict_engine import VerdictEngine


@pytest.fixture
def engine():
    return VerdictEngine()


def make_source(domain, stance, quality_score=60):
    """Create a sample source for verdict tests."""
    return {
        "title": f"Report from {domain}",
        "url": f"https://{domain}/article",
        "stance": stance,
        "quality_score": quality_score,
    }


def test_verified_with_multiple_supporting_sources(engine):
    evidence = [
        make_source("source-a.example", "supports"),
        make_source("source-b.example", "supporting"),
    ]

    result = engine.generate_verdict(
        "A factual claim about a public event.",
        evidence,
    )

    assert result["verdict"] == engine.VERIFIED
    assert result["confidence"] == "medium"
    assert len(result["supporting_sources"]) == 2


def test_false_with_multiple_contradicting_sources(engine):
    evidence = [
        make_source("source-a.example", "contradicts"),
        make_source("source-b.example", "contradiction"),
    ]

    result = engine.generate_verdict(
        "A factual claim about a public event.",
        evidence,
    )

    assert result["verdict"] == engine.FALSE
    assert result["confidence"] == "medium"
    assert len(result["contradicting_sources"]) == 2


def test_mixed_evidence_produces_partial_verdict(engine):
    evidence = [
        make_source("source-a.example", "supports"),
        make_source("source-b.example", "contradicts"),
    ]

    result = engine.generate_verdict(
        "A factual claim about a public event.",
        evidence,
    )

    assert result["verdict"] == engine.PARTIAL


def test_explicit_mixed_stance_produces_partial_verdict(engine):
    evidence = [
        make_source("source-a.example", "mixed"),
    ]

    result = engine.generate_verdict(
        "A factual claim about a public event.",
        evidence,
    )

    assert result["verdict"] == engine.PARTIAL


def test_insufficient_evidence_is_not_false(engine):
    evidence = [
        make_source("source-a.example", "needs_review"),
    ]

    result = engine.generate_verdict(
        "A factual claim about a public event.",
        evidence,
    )

    assert result["verdict"] == engine.UNVERIFIED
    assert result["verdict"] != engine.FALSE


def test_low_quality_sources_do_not_count(engine):
    evidence = [
        make_source("source-a.example", "supports", quality_score=10),
        make_source("source-b.example", "supports", quality_score=20),
    ]

    result = engine.generate_verdict(
        "A factual claim about a public event.",
        evidence,
    )

    assert result["verdict"] == engine.UNVERIFIED
    assert result["supporting_sources"] == []


def test_duplicate_domains_count_as_one_source(engine):
    evidence = [
        {
            "title": "Article One",
            "url": "https://news.example/article-one",
            "stance": "supports",
            "quality_score": 60,
        },
        {
            "title": "Article Two",
            "url": "https://news.example/article-two",
            "stance": "supports",
            "quality_score": 60,
        },
    ]

    result = engine.generate_verdict(
        "A factual claim about a public event.",
        evidence,
    )

    assert result["verdict"] == engine.UNVERIFIED
    assert len(result["supporting_sources"]) == 1


def test_opinion_is_not_fact_checked_as_true_or_false(engine):
    result = engine.generate_verdict(
        "This is the best movie ever made.",
        [],
        claim_type="opinion",
    )

    assert result["verdict"] == engine.OPINION
    assert result["confidence"] == "high"


def test_not_fact_checkable_claim(engine):
    result = engine.generate_verdict(
        "Something unverifiable about a person's private thoughts.",
        [],
        claim_type="not_fact_checkable",
    )

    assert result["verdict"] == engine.OPINION


def test_empty_claim_is_rejected(engine):
    with pytest.raises(ValueError):
        engine.generate_verdict("", [])


def test_non_list_evidence_is_rejected(engine):
    with pytest.raises(TypeError):
        engine.generate_verdict(
            "A factual claim about a public event.",
            "not a list",
        )


def test_invalid_claim_type_is_rejected(engine):
    with pytest.raises(ValueError):
        engine.generate_verdict(
            "A factual claim about a public event.",
            [],
            claim_type="unknown",
        )
