"""Conservative text normalization for submitted claim sources."""
import re
import unicodedata


def clean_text(text: str) -> str:
    """Normalize Unicode and whitespace without changing wording or punctuation."""
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\x00", "")
    text = re.sub(r"[\t\r\f\v]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()
