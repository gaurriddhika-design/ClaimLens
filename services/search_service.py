
import os

import requests


class SearchServiceError(Exception):
    """Raised when the web search service fails."""


class SearchService:
    """Search the web for evidence related to a claim."""

    API_URL = "https://api.tavily.com/search"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")

        if not self.api_key:
            raise SearchServiceError(
                "TAVILY_API_KEY is not configured."
            )

    def search(self, claim: str, max_results: int = 5) -> list[dict]:
        """
        Search for web pages relevant to a claim.

        Each result contains title, url, snippet,
        score, and published_date.
        """
        if not isinstance(claim, str) or not claim.strip():
            raise ValueError("Claim must be a non-empty string.")

        if not isinstance(max_results, int) or isinstance(max_results, bool):
            raise ValueError("max_results must be an integer.")

        if not 1 <= max_results <= 10:
            raise ValueError("max_results must be between 1 and 10.")

        payload = {
            "api_key": self.api_key,
            "query": claim.strip(),
            "search_depth": "basic",
            "max_results": max_results,
            "include_answer": False,
        }

        try:
            response = requests.post(
                self.API_URL,
                json=payload,
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()

        except requests.RequestException as exc:
            raise SearchServiceError(
                f"Web search request failed: {exc}"
            ) from exc

        except ValueError as exc:
            raise SearchServiceError(
                "Search provider returned invalid JSON."
            ) from exc

        if not isinstance(data, dict):
            raise SearchServiceError(
                "Search provider returned an unexpected response."
            )

        raw_results = data.get("results", [])

        if not isinstance(raw_results, list):
            raise SearchServiceError(
                "Search provider returned an invalid results list."
            )

        results = []

        for item in raw_results:
            if not isinstance(item, dict):
                continue

            title = item.get("title")
            url = item.get("url")

            if not isinstance(title, str) or not isinstance(url, str):
                continue

            if not title.strip() or not url.strip():
                continue

            results.append(
                {
                    "title": title.strip(),
                    "url": url.strip(),
                    "snippet": item.get("content", ""),
                    "score": item.get("score"),
                    "published_date": item.get("published_date"),
                }
            )

        return results
