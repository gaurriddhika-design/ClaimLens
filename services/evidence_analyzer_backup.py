
import re


class EvidenceAnalyzer:
    """Identify preliminary evidence signals in source text."""

    STOPWORDS = {
        "a", "an", "the", "is", "are", "was", "were", "be",
        "been", "being", "of", "to", "in", "on", "at", "by",
        "for", "from", "with", "and", "or", "but", "as", "it",
        "this", "that", "these", "those", "has", "have", "had",
        "do", "does", "did", "will", "would", "could", "should",
        "may", "might", "can", "not", "no", "true", "false",
        "claim", "claims", "according", "reported", "report",
        "accurate", "correct", "incorrect", "verified", "confirmed",
        "misleading", "fact", "check",
    }

    CONTRADICTION_PATTERNS = (
        r"\bthe claim is false\b",
        r"\bthe claim is incorrect\b",
        r"\bthe claim is not true\b",
        r"\bthe claim is not correct\b",
        r"\bthe claim was debunked\b",
        r"\bthe claim is misleading\b",
        r"\bno evidence (?:supports|of|for)\b",
        r"\bdid not happen\b",
        r"\bnever happened\b",
        r"\bdenied the claim\b",
        r"\bcontradicts the claim\b",
        r"\bfalse claim\b",
        r"\bthe claim\b.{0,150}?\b(?:is|was)\s+"
        r"(?:false|incorrect|not true|not correct|misleading)\b",
        r"\bthe claim that\b.{0,150}?\b(?:is|was)\s+"
        r"(?:false|incorrect|not true|not correct|misleading)\b",
        r"\bno such (?:ban|policy|law|event|announcement|decision)\b",
    )

    SUPPORT_PATTERNS = (
        r"\bthe claim is true\b",
        r"\bthe claim is accurate\b",
        r"\bthe claim is correct\b",
        r"\bthe claim was verified\b",
        r"\bthe claim was confirmed\b",
        r"\bconfirmed the claim\b",
        r"\bverified the claim\b",
        r"\bthe report is accurate\b",
        r"\bthe report\b.{0,150}?\b(?:is|was)\s+"
        r"(?:accurate|correct|verified|confirmed)\b",
        r"\bthe claim\b.{0,150}?\b(?:is|was)\s+"
        r"(?:true|accurate|correct|verified|confirmed)\b",
    )

    def _tokenize(self, text: str) -> set[str]:
        """Normalize text into meaningful keywords."""
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

    def _contains_pattern(
        self,
        text: str,
        patterns: tuple[str, ...],
    ) -> bool:
        """Check whether text contains a recognized phrase."""
        return any(
            re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
            for pattern in patterns
        )

    def _get_relevant_context(
        self,
        text: str,
        claim_words: set[str],
    ) -> list[str]:
        """
        Return sentences relevant to the claim.

        Include the sentence immediately before or after a relevant
        sentence so that a fact-check conclusion such as
        'The claim is false' is not discarded just because it uses
        different words from the original claim.
        """
        sentences = self._split_sentences(text)

        relevant_indices = [
            index
            for index, sentence in enumerate(sentences)
            if claim_words.intersection(self._tokenize(sentence))
        ]

        if not relevant_indices:
            return []

        included_indices = set()

        for index in relevant_indices:
            included_indices.add(index)

            if index > 0:
                included_indices.add(index - 1)

            if index + 1 < len(sentences):
                included_indices.add(index + 1)

        return [
            sentences[index]
            for index in sorted(included_indices)
        ]

    def analyze_source(self, claim: str, source: dict) -> dict:
        """Analyze one source and return preliminary evidence signals."""
        if not isinstance(claim, str) or not claim.strip():
            raise ValueError("Claim must be a non-empty string.")

        if not isinstance(source, dict):
            raise TypeError("Source must be a dictionary.")

        text = source.get("text") or source.get("snippet") or ""

        if not isinstance(text, str):
            raise TypeError("Source text must be a string.")

        base_result = {
            "title": source.get("title", ""),
            "url": source.get("url", ""),
            "method": "lexical_heuristic",
            "warning": (
                "Preliminary signals only. Phrase matching does not "
                "establish factual truth or understand context."
            ),
        }

        if not text.strip():
            return {
                **base_result,
                "stance": "insufficient_information",
                "relevant_sentences": [],
                "overlap_score": 0.0,
                "matched_keywords": [],
            }

        claim_words = self._tokenize(claim)

        if not claim_words:
            return {
                **base_result,
                "stance": "insufficient_information",
                "relevant_sentences": [],
                "overlap_score": 0.0,
                "matched_keywords": [],
                "warning": "The claim contains no usable keywords.",
            }

        source_words = self._tokenize(text)
        matched_keywords = claim_words.intersection(source_words)

        overlap_score = len(matched_keywords) / len(claim_words)

        relevant_sentences = self._get_relevant_context(
            text,
            claim_words,
        )

        relevant_text = " ".join(relevant_sentences)

        has_contradiction = self._contains_pattern(
            relevant_text,
            self.CONTRADICTION_PATTERNS,
        )

        has_support = self._contains_pattern(
            relevant_text,
            self.SUPPORT_PATTERNS,
        )

        if not relevant_sentences or overlap_score < 0.20:
            stance = "unrelated"
        elif has_contradiction and has_support:
            stance = "mixed"
        elif has_contradiction:
            stance = "potential_contradiction"
        elif has_support:
            stance = "supports"
        else:
            stance = "needs_review"

        return {
            **base_result,
            "stance": stance,
            "relevant_sentences": relevant_sentences[:10],
            "overlap_score": round(overlap_score, 3),
            "matched_keywords": sorted(matched_keywords),
        }

    def analyze(self, claim: str, sources: list[dict]) -> list[dict]:
        """Analyze multiple sources."""
        if not isinstance(sources, list):
            raise TypeError("Sources must be a list.")

        return [
            self.analyze_source(claim, source)
            for source in sources
        ]
