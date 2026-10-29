from io import BytesIO

import pymupdf
import pytest
from fastapi import UploadFile

from app.services.ingestion import ingest_pdf, ingest_text
from app.utils.text_cleaner import clean_text
from app.utils.url_safety import UnsafeURLError, validate_public_http_url


def test_clean_text_normalizes_whitespace_and_unicode():
    assert clean_text("  Hello\t\tworld\r\n  test  ") == "Hello world\ntest"


def test_ingest_text_rejects_blank_text():
    with pytest.raises(ValueError, match="non-whitespace"):
        ingest_text(" \n  ")


def test_ingest_text_preserves_content():
    result = ingest_text("  The Earth orbits the Sun.  ")
    assert result.input_type == "text"
    assert result.text == "The Earth orbits the Sun."


def test_url_safety_rejects_local_and_non_http_urls():
    for url in ("file:///etc/passwd", "http://localhost/", "http://127.0.0.1/", "https://user:pass@example.com"):
        with pytest.raises(UnsafeURLError):
            validate_public_http_url(url)


@pytest.mark.asyncio
async def test_ingest_pdf_extracts_selectable_text():
    memory = BytesIO()
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_text((72, 72), "ClaimLens PDF ingestion test")
        memory.write(doc.tobytes())
    upload = UploadFile(filename="sample.pdf", file=BytesIO(memory.getvalue()))
    result = await ingest_pdf(upload)
    assert result.input_type == "pdf"
    assert result.page_count == 1
    assert "ClaimLens PDF ingestion test" in result.text


@pytest.mark.asyncio
async def test_ingest_pdf_rejects_non_pdf():
    upload = UploadFile(filename="notes.txt", file=BytesIO(b"not a PDF"))
    with pytest.raises(ValueError, match=r"\.pdf"):
        await ingest_pdf(upload)


def test_visible_text_parser_ignores_script_contents_even_with_unrelated_closing_tag():
    from app.services.ingestion import _VisibleTextParser

    parser = _VisibleTextParser()
    parser.feed("<script>secret</div>still-secret</script><p>visible text</p>")
    assert "visible text" in "".join(parser.parts)
    assert "secret" not in "".join(parser.parts)
