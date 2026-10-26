
import ipaddress
import socket
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


class SourceFetcherError(Exception):
    """Raised when a webpage cannot be fetched safely."""


class SourceFetcher:
    """Safely retrieve and extract readable webpage content."""

    MAX_CONTENT_SIZE = 2 * 1024 * 1024  # 2 MB
    TIMEOUT = 10

    def _validate_url(self, url: str) -> str:
        """Validate a public HTTP or HTTPS URL."""

        if not isinstance(url, str) or not url.strip():
            raise SourceFetcherError("URL must be a non-empty string.")

        parsed = urlparse(url.strip())

        if parsed.scheme not in ("http", "https"):
            raise SourceFetcherError("Only HTTP and HTTPS URLs are allowed.")

        if not parsed.hostname:
            raise SourceFetcherError("URL must contain a hostname.")

        if parsed.username or parsed.password:
            raise SourceFetcherError("URLs containing credentials are not allowed.")

        if parsed.port not in (None, 80, 443):
            raise SourceFetcherError("Non-standard ports are not allowed.")

        hostname = parsed.hostname.lower().rstrip(".")

        if hostname == "localhost" or hostname.endswith(".localhost"):
            raise SourceFetcherError("Localhost URLs are not allowed.")

        if hostname.endswith(".local"):
            raise SourceFetcherError("Local network hostnames are not allowed.")

        try:
            addresses = socket.getaddrinfo(
                hostname,
                parsed.port or (443 if parsed.scheme == "https" else 80),
                type=socket.SOCK_STREAM,
            )
        except socket.gaierror as exc:
            raise SourceFetcherError("Could not resolve the URL hostname.") from exc

        if not addresses:
            raise SourceFetcherError("Hostname did not resolve to an IP address.")

        for address in addresses:
            ip = ipaddress.ip_address(address[4][0])

            if not ip.is_global:
                raise SourceFetcherError(
                    "URLs resolving to non-public IP addresses are not allowed."
                )

        return url.strip()

    def fetch(self, url: str) -> dict:
        """
        Fetch a public HTML page and extract its readable content.

        Returns:
            A dictionary containing url, title, text,
            published_date, and fetched_at.
        """
        safe_url = self._validate_url(url)

        try:
            with requests.get(
                safe_url,
                timeout=self.TIMEOUT,
                stream=True,
                allow_redirects=False,
                headers={
                    "User-Agent": "ClaimVerificationBot/1.0",
                    "Accept": "text/html",
                },
            ) as response:

                if 300 <= response.status_code < 400:
                    raise SourceFetcherError(
                        "Redirects are not followed for security reasons."
                    )

                response.raise_for_status()

                content_type = response.headers.get("Content-Type", "")

                if "text/html" not in content_type.lower():
                    raise SourceFetcherError(
                        "The URL did not return an HTML webpage."
                    )

                content_length = response.headers.get("Content-Length")

                if content_length:
                    try:
                        if int(content_length) > self.MAX_CONTENT_SIZE:
                            raise SourceFetcherError(
                                "Webpage exceeds the 2 MB size limit."
                            )
                    except ValueError as exc:
                        raise SourceFetcherError(
                            "Invalid Content-Length header."
                        ) from exc

                chunks = []
                total_size = 0

                for chunk in response.iter_content(chunk_size=8192):
                    if not chunk:
                        continue

                    total_size += len(chunk)

                    if total_size > self.MAX_CONTENT_SIZE:
                        raise SourceFetcherError(
                            "Downloaded webpage exceeds the 2 MB size limit."
                        )

                    chunks.append(chunk)

                html = b"".join(chunks).decode(
                    response.encoding or "utf-8",
                    errors="replace",
                )

        except SourceFetcherError:
            raise
        except requests.RequestException as exc:
            raise SourceFetcherError(
                f"Failed to fetch webpage: {exc}"
            ) from exc

        soup = BeautifulSoup(html, "html.parser")

        title_tag = soup.find("title")
        title = title_tag.get_text(" ", strip=True) if title_tag else ""

        # Remove elements that do not normally contain article text.
        for element in soup(
            ["script", "style", "noscript", "nav", "footer", "header"]
        ):
            element.decompose()

        article = soup.find("article") or soup.find("main") or soup.body or soup

        text = article.get_text(" ", strip=True)

        published_date = None

        date_tag = soup.find(
            "meta",
            attrs={"property": "article:published_time"},
        )

        if date_tag:
            published_date = date_tag.get("content")

        if not published_date:
            date_tag = soup.find(
                "meta",
                attrs={"name": "date"},
            )

            if date_tag:
                published_date = date_tag.get("content")

        return {
            "url": safe_url,
            "title": title,
            "text": text,
            "published_date": published_date,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
