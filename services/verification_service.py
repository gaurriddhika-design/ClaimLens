
from services.claim_extractor import ClaimExtractor
from services.search_service import SearchService, SearchServiceError
from services.source_fetcher import SourceFetcher, SourceFetcherError
from services.evidence_analyzer import EvidenceAnalyzer
from services.source_scorer import SourceScorer
from services.verdict_engine import VerdictEngine


class VerificationService:
    """Coordinate the complete claim-verification workflow."""

    def __init__(
        self,
        search_service=None,
        source_fetcher=None,
        evidence_analyzer=None,
        source_scorer=None,
        verdict_engine=None,
    ):
        
        # Dependency injection lets us replace services in unit tests.
        self.claim_extractor = ClaimExtractor()
        self.search_service = search_service or SearchService()
        self.source_fetcher = source_fetcher or SourceFetcher()
        self.evidence_analyzer = evidence_analyzer or EvidenceAnalyzer()
        self.source_scorer = source_scorer or SourceScorer()
        self.verdict_engine = verdict_engine or VerdictEngine()

    def verify(
        self,
        submitted_text: str,
        max_results: int = 5,
        claim_type: str = "factual",
    ) -> dict:
        """Verify a submitted claim and return its evidence and verdict."""

        # Step 1: Clean and validate the submitted claim.
        claim = self.claim_extractor.extract_claim(submitted_text)

        # Step 2: Find candidate webpages.
        search_results = self.search_service.search(
            claim,
            max_results=max_results,
        )

        analyzed_sources = []
        fetch_failures = []

        # Step 3: Fetch and analyze each candidate source.
        for result in search_results:
            url = result.get("url", "")
            source_content = None
            fetch_error = None

            try:
                source_content = self.source_fetcher.fetch(url)

            except SourceFetcherError as exc:
                fetch_error = str(exc)
                fetch_failures.append({
                    "url": url,
                    "reason": fetch_error,
                })

            # If fetching fails, use the search result snippet as a
            # fallback. A snippet is weaker evidence than full page text.
            if source_content is None:
                source_content = {
                    "url": url,
                    "title": result.get("title", ""),
                    "text": result.get("snippet", ""),
                    "snippet": result.get("snippet", ""),
                    "published_date": result.get("published_date"),
                }

            # Preserve the search provider's relevance score separately.
            source_content["search_score"] = result.get("score")
            source_content["fetch_error"] = fetch_error
            source_content["content_origin"] = (
                "webpage" if fetch_error is None else "search_snippet"
            )

            # Step 4: Analyze the source's relationship to the claim.
            analysis = self.evidence_analyzer.analyze_source(
                claim,
                source_content,
            )

            # Step 5: Score observable source-quality indicators.
            quality = self.source_scorer.score_source(source_content)

            analyzed_sources.append({
                **analysis,
                "quality_score": quality["quality_score"],
                "source_quality": quality,
                "search_score": source_content["search_score"],
                "content_origin": source_content["content_origin"],
                "fetch_error": fetch_error,
                "published_date": source_content.get("published_date"),
                "fetched_at": source_content.get("fetched_at"),
            })

        # Step 6: Generate a cautious claim-level verdict.
        verdict = self.verdict_engine.generate_verdict(
            claim=claim,
            evidence=analyzed_sources,
            claim_type=claim_type,
        )

        limitations = list(verdict["limitations"])

        if fetch_failures:
            limitations.append(
                "Some webpages could not be fetched. Their search snippets, "
                "when available, were used as fallbacks."
            )

        limitations.append(
            "Evidence analysis currently uses basic lexical heuristics. "
            "The result requires human review and is not a definitive fact-check."
        )

        return {
            "claim": claim,
            "verdict": verdict["verdict"],
            "confidence": verdict["confidence"],
            "reason": verdict["reason"],
            "supporting_sources": verdict["supporting_sources"],
            "contradicting_sources": verdict["contradicting_sources"],
            "sources": analyzed_sources,
            "source_count": len(analyzed_sources),
            "fetch_failures": fetch_failures,
            "limitations": limitations,
        }
