
import re


class ClaimExtractor:
    """Extract and validate a claim from user-submitted text."""

    def extract_claim(self, text: str) -> str:
        """
        Clean user input and extract the main claim.

        Args:
            text: Text submitted by the user.

        Returns:
            A cleaned claim suitable for verification.

        Raises:
            TypeError: If the input is not a string.
            ValueError: If the input is empty or too short.
        """
        if not isinstance(text, str):
            raise TypeError("Claim input must be a string.")

        # Remove unnecessary spaces and line breaks.
        text = re.sub(r"\s+", " ", text).strip()

        if not text:
            raise ValueError("Claim cannot be empty.")

        # Remove common introductory phrases.
        text = re.sub(
            r"^(?:breaking news|viral claim|fact check)\s*[:,-]\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )

        # Remove common questions asking for verification.
        text = re.sub(
            r"\s+(?:is this true|is this real|"
            r"can you verify this|fact check this)\??\s*$",
            "",
            text,
            flags=re.IGNORECASE,
        )

        # Remove repeated spaces left after cleaning.
        text = re.sub(r"\s+", " ", text).strip()

        if len(text) < 10:
            raise ValueError(
                "Claim is too short to verify meaningfully."
            )

        return text
