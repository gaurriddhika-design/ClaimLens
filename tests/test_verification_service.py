
import pytest
from unittest.mock import Mock

from services.source_fetcher import SourceFetcherError
from services.verification_service import VerificationService
from services.verdict_engine import VerdictEngine


@pytest.fixture
def mock_services():
    """Create mocked dependencies without network requests."""
    search = Mock()
    fetcher = Mock()
    analyzer = Mock()
    scorer = Mock()

    service = VerificationService(
        search_service=search,
        source_fetcher=fetcher,
        evidence_analyzer=analyzer,
        source_scorer=scorer,
        verdict_engine=VerdictEngine(),
    )

    return service, search, fetcher, analyzer, scorer


def test_verify_returns_verified_result(mock_services):
    service, search, fetcher, analyzer, scorer = mock_services

    search.search.return_value = [
        {
            "title": "Report A",
            "url": "https://source-a.example/article",
            "snippet": "Sample evidence A",
            "score": 0.95,
            "published_date": "2026-10-20",
        },
        {
            "title": "Report B",
            "url": "https://source-b.example/article",
            "snippet": "Sample evidence B",
            "score": 0.90,
            "published_date": "2026-10-21",
        },
    ]

    fetcher.fetch.side_effect = [
        {
            "title": "Report A",
            "url": "https://source-a.example/article",
            "text": "Detailed report A content.",
            "published_date": "2026-10-20",
            "fetched_at": "2026-10-22T10:00:00+00:00",
        },
        {
            "title": "Report B",
            "url": "https://source-b.example/article",
            "text": "Detailed report B content.",
            "published_date": "2026-10-21",
            "fetched_at": "2026-10-22T10:00:00+00:00",
        },
    ]

    analyzer.analyze_source.side_effect = [
        {
            "title": "Report A",
            "url": "https://source-a.example/article",
            "stance": "supports",
            "relevant_sentences": ["Report A supports the claim."],
            "overlap_score": 0.8,
            "method": "test_mock",
        },
        {
            "title": "Report B",
            "url": "https://source-b.example/article",
            "stance": "supports",
            "relevant_sentences": ["Report B supports the claim."],
            "overlap_score": 0.7,
            "method": "test_mock",
        },
    ]

    scorer.score_source.return_value = {
        "quality_score": 50,
        "indicators": [],
        "text_length": 100,
        "method": "test_mock",
        "warning": "Synthetic test score.",
    }

    result = service.verify(
        "The government announced a new policy today.",
        max_results=2,
    )

    assert result["verdict"] == VerdictEngine.VERIFIED
    assert result["source_count"] == 2
    assert len(result["supporting_sources"]) == 2
    assert result["fetch_failures"] == []

    search.search.assert_called_once()
    assert fetcher.fetch.call_count == 2
    assert analyzer.analyze_source.call_count == 2
    assert scorer.score_source.call_count == 2


def test_verify_uses_snippet_when_fetch_fails(mock_services):
    service, search, fetcher, analyzer, scorer = mock_services

    search.search.return_value = [
        {
            "title": "Search Result",
            "url": "https://source-a.example/article",
            "snippet": "A short search result snippet.",
            "score": 0.8,
            "published_date": None,
        }
    ]

    fetcher.fetch.side_effect = SourceFetcherError(
        "Test fetch failure"
    )

    analyzer.analyze_source.return_value = {
        "title": "Search Result",
        "url": "https://source-a.example/article",
        "stance": "needs_review",
        "relevant_sentences": [],
        "overlap_score": 0.4,
        "method": "test_mock",
    }

    scorer.score_source.return_value = {
        "quality_score": 40,
        "indicators": [],
        "text_length": 30,
        "method": "test_mock",
        "warning": "Synthetic test score.",
    }

    result = service.verify(
        "The government announced a new policy today.",
        max_results=1,
    )

    assert result["source_count"] == 1
    assert len(result["fetch_failures"]) == 1
    assert result["sources"][0]["content_origin"] == "search_snippet"
    assert result["verdict"] == VerdictEngine.UNVERIFIED
    assert any(
        "could not be fetched" in limitation
        for limitation in result["limitations"]
    )


def test_verify_rejects_empty_claim_before_search(mock_services):
    service, search, fetcher, analyzer, scorer = mock_services

    with pytest.raises(ValueError):
        service.verify("   ")

    search.search.assert_not_called()
    fetcher.fetch.assert_not_called()


def test_verify_returns_unverified_when_no_results(mock_services):
    service, search, fetcher, analyzer, scorer = mock_services

    search.search.return_value = []

    result = service.verify(
        "The government announced a new policy today."
    )

    assert result["verdict"] == VerdictEngine.UNVERIFIED
    assert result["source_count"] == 0
    assert result["sources"] == []
    assert result["fetch_failures"] == []

    fetcher.fetch.assert_not_called()
    analyzer.analyze_source.assert_not_called()
    scorer.score_source.assert_not_called()
