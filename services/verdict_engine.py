
from urllib.parse import urlparse


class VerdictEngine:
    """Generate a cautious claim-level verdict from evidence signals."""

    VERIFIED = "Verified"
    FALSE = "False / Contradicted"
    PARTIAL = "Partially True / Misleading"
    UNVERIFIED = "Unverified / Insufficient Evidence"
    OPINION = "Opinion / Not Fact-Checkable"

    MIN_SOURCE_QUALITY = 30
    MIN_INDEPENDENT_SOURCES = 2

    SUPPORTING_STANCES = {
        "support",
        "supports",
        "supporting",
        "consistent",
    }

    CONTRADICTING_STANCES = {
        "contradiction",
        "contradicts",
        "contradicting",
        "potential_contradiction",
    }

    MIXED_STANCES = {
        "mixed",
        "partially_supports",
        "partially_contradicts",
    }

    def _get_domain(self, url: str) -> str:
        """Return a normalized hostname for source deduplication."""
        try:
            return (urlparse(url).hostname or "").lower().rstrip(".")
        except (TypeError, ValueError):
            return ""

    def _unique_sources(self, sources: list[dict]) -> list[dict]:
        """Keep only one entry per hostname."""
        unique = {}
        for source in sources:
            domain = self._get_domain(source.get("url", ""))

            if domain:
                unique.setdefault(domain, source)

        return list(unique.values())

    def generate_verdict(
        self,
        claim: str,
        evidence: list[dict],
        claim_type: str = "factual",
    ) -> dict:
        """
        Generate a verdict from analyzed evidence.

        Expected evidence fields:
            stance: supporting, contradicting, mixed, or another signal
            url: source URL
            quality_score: source-quality indicator score from SourceScorer

        Unknown or preliminary stances are not treated as proof.
        """
        if not isinstance(claim, str) or not claim.strip():
            raise ValueError("Claim must be a non-empty string.")

        if not isinstance(evidence, list):
            raise TypeError("Evidence must be a list.")

        if claim_type not in {"factual", "opinion", "not_fact_checkable"}:
            raise ValueError(
                "claim_type must be factual, opinion, or not_fact_checkable."
            )

        if claim_type in {"opinion", "not_fact_checkable"}:
            return {
                "claim": claim.strip(),
                "verdict": self.OPINION,
                "confidence": "high",
                "reason": (
                    "The claim was classified as opinion or not fact-checkable. "
                    "A factual verdict is not appropriate."
                ),
                "supporting_sources": [],
                "contradicting_sources": [],
                "limitations": [
                    "This classification was supplied to the verdict engine; "
                    "the engine does not automatically detect opinions."
                ],
            }

        valid_evidence = [
            item for item in evidence
            if isinstance(item, dict)
        ]

        # Only sources meeting the minimum indicator score are counted
        # toward a verdict. This is a heuristic filter, not proof of reliability.
        eligible = [
            item for item in valid_evidence
            if isinstance(item.get("quality_score"), (int, float))
            and not isinstance(item.get("quality_score"), bool)
            and item["quality_score"] >= self.MIN_SOURCE_QUALITY
        ]

        supporting = self._unique_sources([
            item for item in eligible
            if str(item.get("stance", "")).lower()
            in self.SUPPORTING_STANCES
        ])

        contradicting = self._unique_sources([
            item for item in eligible
            if str(item.get("stance", "")).lower()
            in self.CONTRADICTING_STANCES
        ])

        mixed = self._unique_sources([
            item for item in eligible
            if str(item.get("stance", "")).lower()
            in self.MIXED_STANCES
        ])

        support_count = len(supporting)
        contradiction_count = len(contradicting)

        verdict = self.UNVERIFIED
        confidence = "low"
        reason = (
            "The available evidence does not establish the claim as true or false."
        )

        if mixed or (support_count > 0 and contradiction_count > 0):
            verdict = self.PARTIAL
            confidence = "low"
            reason = (
                "The evidence contains mixed signals. The claim may be partly "
                "accurate, misleading, or missing important context; this "
                "requires closer review."
            )

        elif (
            support_count >= self.MIN_INDEPENDENT_SOURCES
            and contradiction_count == 0
        ):
            verdict = self.VERIFIED
            confidence = "medium"
            reason = (
                "Multiple distinct source domains provide supporting signals, "
                "with no qualifying contradictory source in the supplied evidence."
            )

        elif (
            contradiction_count >= self.MIN_INDEPENDENT_SOURCES
            and support_count == 0
        ):
            verdict = self.FALSE
            confidence = "medium"
            reason = (
                "Multiple distinct source domains provide contradictory signals, "
                "with no qualifying supporting source in the supplied evidence."
            )

        limitations = [
            "Verdicts depend on the quality and completeness of the supplied evidence.",
            "Different domains do not guarantee independent reporting.",
            "Source-quality scores are heuristic indicators, not truth probabilities.",
            "Preliminary keyword-based evidence signals cannot establish factual truth.",
        ]

        if not eligible:
            limitations.append(
                "No evidence met the minimum source-quality indicator threshold."
            )

        if (
            support_count < self.MIN_INDEPENDENT_SOURCES
            and contradiction_count < self.MIN_INDEPENDENT_SOURCES
            and not mixed
            and not (support_count and contradiction_count)
        ):
            limitations.append(
                "There are not enough distinct qualifying sources for a stronger verdict."
            )

        return {
            "claim": claim.strip(),
            "verdict": verdict,
            "confidence": confidence,
            "reason": reason,
            "supporting_sources": [
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                }
                for item in supporting
            ],
            "contradicting_sources": [
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                }
                for item in contradicting
            ],
            "limitations": limitations,
        }
