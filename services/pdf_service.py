from io import BytesIO

import pymupdf
import pytesseract
from PIL import Image
from pypdf import PdfReader

pytesseract.pytesseract.tesseract_cmd = (
    r"D:\ocr\tesseract.exe"
)


def has_meaningful_text(text: str) -> bool:
    meaningful_chars = sum(
        1 for char in text if char.isalnum()
    )
    return meaningful_chars >= 20


def extract_pdf_text(pdf_bytes: bytes) -> str:
    if not pdf_bytes:
        raise ValueError("The uploaded PDF is empty.")

    ocr_document = None

    try:
        reader = PdfReader(
            BytesIO(pdf_bytes),
            strict=False
        )

        if reader.is_encrypted:
            raise ValueError(
                "Password-protected PDFs are not supported."
            )

        extracted_pages = [
            page.extract_text() or ""
            for page in reader.pages
        ]

        final_pages = []

        for page_number, text in enumerate(extracted_pages):
            if has_meaningful_text(text):
                final_pages.append(text)
                continue

            if ocr_document is None:
                ocr_document = pymupdf.open(
                    stream=pdf_bytes,
                    filetype="pdf"
                )

            page = ocr_document[page_number]
            pixmap = page.get_pixmap(dpi=200)

            image = Image.open(
                BytesIO(pixmap.tobytes("png"))
            )

            ocr_text = pytesseract.image_to_string(
                image,
                lang="eng"
            )

            final_pages.append(
                ocr_text if has_meaningful_text(ocr_text)
                else ""
            )

        combined_text = "\n\n".join(
            text.strip()
            for text in final_pages
            if text.strip()
        )

        if not has_meaningful_text(combined_text):
            raise ValueError(
                "No readable text was found in the PDF."
            )

        return combined_text

    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(
            "Could not read this PDF. Check the file "
            "and make sure Tesseract OCR is installed."
        ) from exc
    finally:
        if ocr_document is not None:
            ocr_document.close()