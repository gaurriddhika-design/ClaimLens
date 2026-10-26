
import re


class EvidenceAnalyzer:
    """Analyze how source text relates to a factual claim."""

    STOPWORDS = {
        "a", "an", "the", "is", "are", "was", "were", "be",
        "been", "being", "of", "to", "in", "on", "at", "by",
        "for", "from", "with", "and", "or", "but", "as", "it",
        "this", "that", "these", "those", "has", "have", "had",
        "do", "does", "did", "will", "would", "could", "should",
        "may", "might", "can", "not", "no", "true", "false",
        "claim", "claims", "according", "reported",
    }

    CONTRADICTION_MARKERS = (
        "false",
        "incorrect",
        "not true",
        "not correct",
        "debunked",
        "no evidence",
        "did not happen",
        "never happened",
        "denied the claim",
        "contradicts the claim",
        "misleading claim",
    )

    def _tokenize(self, text: str) -> set[str]:
        """Convert text into normalized, meaningful words."""
        words = re.findall(r"\b[a-z0-9]+\b", text.lower())

        return {
            word
            for word in words
            if len(word) > 1 and word not in self.STOPWORDS
        }

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into approximate sentences."""
        return [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", text)
            if sentence.strip()
        ]

    def analyze_source(self, claim: str, source: dict) -> dict:
        """
        Assess one source using basic lexical heuristics.

        This produces preliminary evidence signals, not a verdict.
        """
        if not isinstance(claim, str) or not claim.strip():
            raise ValueError("Claim must be a non-empty string.")

        if not isinstance(source, dict):
            raise TypeError("Source must be a dictionary.")

        text = source.get("text") or source.get("snippet") or ""

        if not isinstance(text, str):
            raise TypeError("Source text must be a string.")

        if not text.strip():
            return {
                "title": source.get("title", ""),
                "url": source.get("url", ""),
                "stance": "insufficient_information",
                "relevant_sentences": [],
                "overlap_score": 0.0,
                "method": "lexical_heuristic",
                "warning": "No source text was available.",
            }

        claim_words = self._tokenize(claim)
        source_words = self._tokenize(text)

        if not claim_words:
            return {
                "title": source.get("title", ""),
                "url": source.get("url", ""),
                "stance": "insufficient_information",
                "relevant_sentences": [],
                "overlap_score": 0.0,
                "method": "lexical_heuristic",
                "warning": "The claim contains no usable keywords.",
            }

        shared_words = claim_words.intersection(source_words)
        overlap_score = len(shared_words) / len(claim_words)

        sentences = self._split_sentences(text)

        relevant_sentences = []

        for sentence in sentences:
            sentence_words = self._tokenize(sentence)

            if claim_words.intersection(sentence_words):
                relevant_sentences.append(sentence)

        text_lower = text.lower()

        has_contradiction_marker = any(
            marker in text_lower
            for marker in self.CONTRADICTION_MARKERS
        )

        if overlap_score < 0.20:
            stance = "unrelated"
        elif has_contradiction_marker:
            stance = "potential_contradiction"
        else:
            stance = "needs_review"

        return {
            "title": source.get("title", ""),
            "url": source.get("url", ""),
            "stance": stance,
            "relevant_sentences": relevant_sentences[:10],
            "overlap_score": round(overlap_score, 3),
            "matched_keywords": sorted(shared_words),
            "method": "lexical_heuristic",
            "warning": (
                "Preliminary signal only. Keyword overlap and "
                "contradiction phrases do not establish factual truth."
            ),
        }

    def analyze(self, claim: str, sources: list[dict]) -> list[dict]:
        """Analyze multiple sources and return their evidence signals."""
        if not isinstance(sources, list):
            raise TypeError("Sources must be a list.")

        return [
            self.analyze_source(claim, source)
            for source in sources
        ]
