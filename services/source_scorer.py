
from urllib.parse import urlparse


class SourceScorer:
    """Score observable source-quality indicators."""

    def score_source(self, source: dict) -> dict:
        """
        Evaluate source-quality indicators.

        The score is a heuristic, not a probability that
        the source or its claims are truthful.
        """
        if not isinstance(source, dict):
            raise TypeError("Source must be a dictionary.")

        url = source.get("url") or ""
        title = source.get("title") or ""
        text = source.get("text") or source.get("snippet") or ""
        published_date = source.get("published_date")

        if not isinstance(url, str):
            raise TypeError("Source URL must be a string.")

        if not isinstance(title, str):
            raise TypeError("Source title must be a string.")

        if not isinstance(text, str):
            raise TypeError("Source text must be a string.")

        score = 0
        indicators = []

        parsed_url = urlparse(url)
        hostname = (parsed_url.hostname or "").lower().rstrip(".")

        # A valid-looking URL helps identify the source.
        if parsed_url.scheme in ("http", "https") and hostname:
            score += 10
            indicators.append({
                "name": "valid_web_address",
                "points": 10,
                "reason": "The source has an HTTP or HTTPS URL with a hostname.",
            })

        # HTTPS protects data in transit; it does not prove truthfulness.
        if parsed_url.scheme == "https":
            score += 10
            indicators.append({
                "name": "https",
                "points": 10,
                "reason": "The connection uses HTTPS, which protects data in transit.",
            })

        # These domains may indicate an official institution.
        # They are indicators, not guarantees of reliability.
        official_suffixes = (
            ".gov",
            ".gov.in",
            ".nic.in",
            ".edu",
            ".edu.in",
        )

        is_official_domain = (
            hostname in ("gov", "edu")
            or hostname.endswith(official_suffixes)
        )

        if is_official_domain:
            score += 25
            indicators.append({
                "name": "official_domain_pattern",
                "points": 25,
                "reason": (
                    "The hostname matches a government or educational "
                    "domain pattern. Verify the institution and page."
                ),
            })

        if title.strip():
            score += 10
            indicators.append({
                "name": "page_title",
                "points": 10,
                "reason": "The source provides a page title.",
            })

        if isinstance(published_date, str) and published_date.strip():
            score += 15
            indicators.append({
                "name": "publication_date",
                "points": 15,
                "reason": "A publication date is available for checking recency.",
            })

        text_length = len(text.strip())

        if text_length >= 500:
            score += 20
            indicators.append({
                "name": "substantial_content",
                "points": 20,
                "reason": "The extracted source text contains at least 500 characters.",
            })
        elif text_length >= 150:
            score += 10
            indicators.append({
                "name": "some_content",
                "points": 10,
                "reason": "The extracted source text contains at least 150 characters.",
            })

        return {
            "title": title,
            "url": url,
            "quality_score": min(score, 100),
            "indicators": indicators,
            "text_length": text_length,
            "method": "rule_based_source_assessment",
            "warning": (
                "This score measures observable quality indicators, "
                "not factual accuracy. Check the publisher, context, "
                "date, and evidence before drawing conclusions."
            ),
        }

    def score_sources(self, sources: list[dict]) -> list[dict]:
        """Score multiple sources and sort them by indicator score."""
        if not isinstance(sources, list):
            raise TypeError("Sources must be a list.")

        scored_sources = [
            self.score_source(source)
            for source in sources
        ]

        return sorted(
            scored_sources,
            key=lambda item: item["quality_score"],
            reverse=True,
        )
