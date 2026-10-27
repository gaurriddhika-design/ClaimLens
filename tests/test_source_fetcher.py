
import socket
from unittest.mock import MagicMock

import pytest
import requests

from services.source_fetcher import SourceFetcher, SourceFetcherError


@pytest.fixture
def fetcher():
    return SourceFetcher()


@pytest.fixture
def public_dns(monkeypatch):
    """Pretend the hostname resolves to a public IP address."""
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                6,
                "",
                ("93.184.216.34", 80),
            )
        ],
    )


def make_response(
    status_code=200,
    headers=None,
    chunks=None,
    encoding="utf-8",
):
    """Create a fake HTTP response without accessing the internet."""
    response = MagicMock()
    response.status_code = status_code
    response.headers = headers or {"Content-Type": "text/html"}
    response.encoding = encoding
    response.iter_content.return_value = (
        chunks if chunks is not None else [b"<html><title>Test</title></html>"]
    )
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


# ---------------- URL validation tests ----------------


@pytest.mark.parametrize(
    "url",
    [
        "",
        "   ",
        None,
        123,
        "ftp://example.com",
        "javascript:alert(1)",
        "https:///missing-host",
        "https://user:password@example.com",
        "http://example.com:8080",
        "http://localhost",
        "http://sub.localhost",
        "http://printer.local",
    ],
)
def test_rejects_invalid_or_unsafe_urls(fetcher, url):
    with pytest.raises(SourceFetcherError):
        fetcher._validate_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1",
        "http://192.168.1.10",
        "http://10.0.0.5",
    ],
)
def test_rejects_non_public_ip_addresses(fetcher, monkeypatch, url):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                6,
                "",
                (url.split("//")[1], 80),
            )
        ],
    )

    with pytest.raises(SourceFetcherError):
        fetcher._validate_url(url)


def test_dns_resolution_failure_is_handled(fetcher, monkeypatch):
    def fail_dns(*args, **kwargs):
        raise socket.gaierror("DNS lookup failed")

    monkeypatch.setattr(socket, "getaddrinfo", fail_dns)

    with pytest.raises(SourceFetcherError, match="resolve"):
        fetcher._validate_url("https://example.com")


def test_accepts_public_http_url(fetcher, public_dns):
    url = "https://example.com/article"

    assert fetcher._validate_url(url) == url


# ---------------- Successful fetching tests ----------------


def test_fetch_extracts_title_and_article_text(
    fetcher, public_dns, monkeypatch
):
    html = b"""
    <html>
      <head>
        <title>Example News</title>
        <meta property="article:published_time"
              content="2026-10-25T10:00:00Z">
      </head>
      <body>
        <nav>Navigation text</nav>
        <article>
          <h1>Important Claim</h1>
          <p>This is the article content.</p>
        </article>
        <script>ignore_this_script()</script>
        <footer>Footer text</footer>
      </body>
    </html>
    """

    response = make_response(
        headers={"Content-Type": "text/html; charset=utf-8"},
        chunks=[html],
    )

    monkeypatch.setattr(requests, "get", lambda *a, **kw: response)

    result = fetcher.fetch("https://example.com/article")

    assert result["url"] == "https://example.com/article"
    assert result["title"] == "Example News"
    assert "Important Claim" in result["text"]
    assert "This is the article content." in result["text"]
    assert "ignore_this_script" not in result["text"]
    assert "Navigation text" not in result["text"]
    assert "Footer text" not in result["text"]
    assert result["published_date"] == "2026-10-25T10:00:00Z"
    assert result["fetched_at"]


def test_fetch_uses_fallback_date_metadata(
    fetcher, public_dns, monkeypatch
):
    html = b"""
    <html>
      <head>
        <meta name="date" content="2026-10-20">
      </head>
      <body><p>Article content</p></body>
    </html>
    """

    response = make_response(chunks=[html])
    monkeypatch.setattr(requests, "get", lambda *a, **kw: response)

    result = fetcher.fetch("https://example.com/article")

    assert result["published_date"] == "2026-10-20"


def test_fetch_handles_page_without_title(
    fetcher, public_dns, monkeypatch
):
    response = make_response(
        chunks=[b"<html><body><p>Article text</p></body></html>"]
    )
    monkeypatch.setattr(requests, "get", lambda *a, **kw: response)

    result = fetcher.fetch("https://example.com/article")

    assert result["title"] == ""
    assert "Article text" in result["text"]


# ---------------- HTTP response safety tests ----------------


def test_rejects_redirects(fetcher, public_dns, monkeypatch):
    response = make_response(status_code=302)
    response.headers = {
        "Content-Type": "text/html",
        "Location": "http://127.0.0.1",
    }
    monkeypatch.setattr(requests, "get", lambda *a, **kw: response)

    with pytest.raises(SourceFetcherError, match="Redirects"):
        fetcher.fetch("https://example.com/article")


def test_rejects_non_html_content(
    fetcher, public_dns, monkeypatch
):
    response = make_response(
        headers={"Content-Type": "application/pdf"}
    )
    monkeypatch.setattr(requests, "get", lambda *a, **kw: response)

    with pytest.raises(SourceFetcherError, match="HTML"):
        fetcher.fetch("https://example.com/document")


def test_rejects_oversized_content_length(
    fetcher, public_dns, monkeypatch
):
    response = make_response(
        headers={
            "Content-Type": "text/html",
            "Content-Length": str(SourceFetcher.MAX_CONTENT_SIZE + 1),
        }
    )
    monkeypatch.setattr(requests, "get", lambda *a, **kw: response)

    with pytest.raises(SourceFetcherError, match="2 MB"):
        fetcher.fetch("https://example.com/article")


def test_rejects_invalid_content_length(
    fetcher, public_dns, monkeypatch
):
    response = make_response(
        headers={
            "Content-Type": "text/html",
            "Content-Length": "not-a-number",
        }
    )
    monkeypatch.setattr(requests, "get", lambda *a, **kw: response)

    with pytest.raises(SourceFetcherError, match="Content-Length"):
        fetcher.fetch("https://example.com/article")


def test_rejects_stream_larger_than_limit(
    fetcher, public_dns, monkeypatch
):
    response = make_response(
        chunks=[
            b"a" * 8192,
            b"b" * SourceFetcher.MAX_CONTENT_SIZE,
        ]
    )
    monkeypatch.setattr(requests, "get", lambda *a, **kw: response)

    with pytest.raises(SourceFetcherError, match="2 MB"):
        fetcher.fetch("https://example.com/article")


# ---------------- Network error tests ----------------


def test_handles_http_error(fetcher, public_dns, monkeypatch):
    response = make_response(status_code=500)
    response.raise_for_status.side_effect = requests.HTTPError(
        "Internal server error"
    )
    monkeypatch.setattr(requests, "get", lambda *a, **kw: response)

    with pytest.raises(SourceFetcherError, match="Failed to fetch"):
        fetcher.fetch("https://example.com/article")


def test_handles_network_timeout(fetcher, public_dns, monkeypatch):
    def timeout(*args, **kwargs):
        raise requests.Timeout("Request timed out")

    monkeypatch.setattr(requests, "get", timeout)

    with pytest.raises(SourceFetcherError, match="Failed to fetch"):
        fetcher.fetch("https://example.com/article")


def test_handles_connection_error(fetcher, public_dns, monkeypatch):
    def connection_failure(*args, **kwargs):
        raise requests.ConnectionError("Connection failed")

    monkeypatch.setattr(requests, "get", connection_failure)

    with pytest.raises(SourceFetcherError, match="Failed to fetch"):
        fetcher.fetch("https://example.com/article")
