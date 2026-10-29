"""Input ingestion for text, PDF uploads, and public web pages.

This module extracts and validates input only. It does not verify claims or invent
factual conclusions; the separate verification engine will consume IngestedDocument.
"""

from PIL import Image, UnidentifiedImageError
import pytesseract
from .pdf_service import extract_pdf_text
from dataclasses import dataclass
from html.parser import HTMLParser
from io import BytesIO
from urllib.parse import urljoin

import pymupdf
import httpx
from fastapi import UploadFile

from ..core.config import settings
from ..utils.text_cleaner import clean_text
from ..utils.url_safety import UnsafeURLError, validate_public_http_url


@dataclass(frozen=True)
class IngestedDocument:
    input_type: str
    text: str
    summary: str
    source_url: str | None = None
    page_count: int | None = None


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip_tags = {"script", "style", "noscript", "svg", "template"}
        self._skip_stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if self._skip_stack:
            if tag in self._skip_tags:
                self._skip_stack.append(tag)
        elif tag in self._skip_tags:
            self._skip_stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self._skip_stack:
            # Only close the matching skipped element; malformed unrelated end tags
            # must not accidentally expose script/style contents.
            if tag == self._skip_stack[-1]:
                self._skip_stack.pop()
            return
        if tag in {"p", "div", "article", "section", "br", "li", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip_stack:
            self.parts.append(data)


def ingest_text(text: str) -> IngestedDocument:
    cleaned = clean_text(text)
    if not cleaned:
        raise ValueError("Text must contain non-whitespace characters.")
    if len(cleaned) > settings.max_text_chars:
        raise ValueError(f"Text exceeds the {settings.max_text_chars}-character limit.")
    return IngestedDocument("text", cleaned, cleaned[:240])


async def ingest_pdf(upload: UploadFile) -> IngestedDocument:
    name = (upload.filename or "").lower()

    if not name.endswith(".pdf"):
        raise ValueError("Upload must have a .pdf filename.")

    max_bytes = settings.max_upload_mb * 1024 * 1024
    content = await upload.read(max_bytes + 1)

    if len(content) > max_bytes:
        raise ValueError(
            f"PDF exceeds the {settings.max_upload_mb} MB upload limit."
        )

    if not content.startswith(b"%PDF-"):
        raise ValueError(
            "Uploaded file does not appear to be a valid PDF."
        )

    try:
        with pymupdf.open(
            stream=BytesIO(content),
            filetype="pdf"
        ) as document:
            if document.is_encrypted:
                raise ValueError(
                    "Password-protected PDFs are not supported."
                )

            page_count = document.page_count

            if page_count == 0:
                raise ValueError("PDF contains no pages.")

            if page_count > settings.max_pdf_pages:
                raise ValueError(
                    f"PDF exceeds the {settings.max_pdf_pages}-page limit."
                )

        text = extract_pdf_text(content)
        text = clean_text(text)

    except ValueError:
        raise
    except pymupdf.FileDataError as exc:
        raise ValueError("PDF could not be read.") from exc

    if not text:
        raise ValueError("No readable text was extracted from this PDF.")

    if len(text) > settings.max_text_chars:
        raise ValueError(
            f"Extracted PDF text exceeds the "
            f"{settings.max_text_chars}-character limit."
        )

    return IngestedDocument(
        "pdf",
        text,
        text[:240],
        page_count=page_count
    )

async def ingest_image(upload: UploadFile) -> IngestedDocument:
    max_bytes = settings.max_upload_mb * 1024 * 1024
    content = await upload.read(max_bytes + 1)

    if not content:
        raise ValueError("Uploaded image is empty.")

    if len(content) > max_bytes:
        raise ValueError(
            f"Image exceeds the {settings.max_upload_mb} MB upload limit."
        )

    try:
        with Image.open(BytesIO(content)) as image:
            if image.format not in {"PNG", "JPEG", "WEBP"}:
                raise ValueError("Only PNG, JPG, JPEG, and WEBP images are supported.")

            if image.width * image.height > 25_000_000:
                raise ValueError("Image dimensions are too large.")

            image.load()
            image = image.convert("RGB")
            text = pytesseract.image_to_string(image)

    except ValueError:
        raise
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("Uploaded file is not a readable image.") from exc

    text = clean_text(text)

    if not text:
        raise ValueError("No readable text was extracted from this image.")

    if len(text) > settings.max_text_chars:
        raise ValueError(
            f"Extracted image text exceeds the "
            f"{settings.max_text_chars}-character limit."
        )

    return IngestedDocument("image", text, text[:240])



async def ingest_url(url: str) -> IngestedDocument:
    current_url = validate_public_http_url(url)
    timeout = httpx.Timeout(settings.request_timeout_seconds)
    headers = {"User-Agent": "ClaimLens-ResearchBot/0.1 (+text extraction; contact site owner)"}
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False, headers=headers) as client:
        response = None
        for _ in range(4):
            # Revalidate every hop. Redirects are never followed automatically.
            current_url = validate_public_http_url(current_url)
            async with client.stream("GET", current_url, follow_redirects=False) as response:
                if response.status_code in {301, 302, 303, 307, 308}:
                    location = response.headers.get("location")
                    if not location:
                        raise ValueError("Website returned a redirect without a destination.")
                    current_url = urljoin(current_url, location)
                    continue
                response.raise_for_status()
                content_type = response.headers.get("content-type", "").lower()
                if "text/html" not in content_type and "text/plain" not in content_type:
                    raise ValueError("URL must return an HTML or plain-text page.")
                content_length = response.headers.get("content-length")
                if content_length and int(content_length) > settings.max_url_response_bytes:
                    raise ValueError("Website response exceeds the configured download limit.")
                chunks: list[bytes] = []
                total_bytes = 0
                async for chunk in response.aiter_bytes():
                    total_bytes += len(chunk)
                    if total_bytes > settings.max_url_response_bytes:
                        raise ValueError("Website response exceeds the configured download limit.")
                    chunks.append(chunk)
                raw_content = b"".join(chunks)
                encoding = response.encoding or "utf-8"
                break
        else:
            raise ValueError("Website redirected too many times.")
        body = raw_content.decode(encoding, errors="replace")
        if "text/html" in content_type:
            parser = _VisibleTextParser()
            parser.feed(body)
            body = "".join(parser.parts)
        text = clean_text(body)
        if not text:
            raise ValueError("No readable text was extracted from this URL.")
        if len(text) > settings.max_text_chars:
            raise ValueError(f"Extracted URL text exceeds the {settings.max_text_chars}-character limit.")
        return IngestedDocument("url", text, text[:240], source_url=current_url)
