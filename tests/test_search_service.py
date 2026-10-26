
import pytest
import requests
from unittest.mock import Mock, patch

from services.search_service import SearchService, SearchServiceError


@pytest.fixture
def search_service():
    return SearchService(api_key="test-api-key")


@patch("services.search_service.requests.post")
def test_search_returns_normalized_results(mock_post, search_service):
    mock_response = Mock()
    mock_response.json.return_value = {
        "results": [
            {
                "title": "UPI Payment Rules",
                "url": "https://example.com/upi",
                "content": "Information about UPI payment rules.",
                "score": 0.95,
                "published_date": "2026-10-20",
            }
        ]
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    results = search_service.search("UPI payment rules", max_results=1)

    assert len(results) == 1
    assert results[0]["title"] == "UPI Payment Rules"
    assert results[0]["url"] == "https://example.com/upi"
    assert results[0]["snippet"] == "Information about UPI payment rules."
    assert results[0]["score"] == 0.95
    assert results[0]["published_date"] == "2026-10-20"

    mock_post.assert_called_once()


@patch("services.search_service.requests.post")
def test_search_sends_expected_request(mock_post, search_service):
    mock_response = Mock()
    mock_response.json.return_value = {"results": []}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    search_service.search("test claim", max_results=3)

    _, kwargs = mock_post.call_args

    assert kwargs["json"]["api_key"] == "test-api-key"
    assert kwargs["json"]["query"] == "test claim"
    assert kwargs["json"]["max_results"] == 3
    assert kwargs["json"]["include_answer"] is False
    assert kwargs["timeout"] == 15


def test_search_rejects_empty_claim(search_service):
    with pytest.raises(ValueError):
        search_service.search("   ")


@pytest.mark.parametrize("max_results", [0, 11, -1, 1.5, True])
def test_search_rejects_invalid_max_results(search_service, max_results):
    with pytest.raises(ValueError):
        search_service.search("test claim", max_results=max_results)


@patch("services.search_service.requests.post")
def test_search_handles_http_error(mock_post, search_service):
    mock_post.side_effect = requests.Timeout("Request timed out")

    with pytest.raises(SearchServiceError, match="request failed"):
        search_service.search("test claim")


@patch("services.search_service.requests.post")
def test_search_handles_invalid_json(mock_post, search_service):
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_post.return_value = mock_response

    with pytest.raises(SearchServiceError, match="invalid JSON"):
        search_service.search("test claim")


@patch("services.search_service.requests.post")
def test_search_ignores_malformed_results(mock_post, search_service):
    mock_response = Mock()
    mock_response.json.return_value = {
        "results": [
            {
                "title": "Valid Result",
                "url": "https://example.com",
                "content": "Valid content",
            },
            {"title": "Missing URL"},
            "invalid result",
        ]
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    results = search_service.search("test claim")

    assert len(results) == 1
    assert results[0]["title"] == "Valid Result"


def test_search_requires_api_key():
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(SearchServiceError, match="not configured"):
            SearchService(api_key="")
