from pathlib import Path

from services.pdf_service import extract_pdf_text

pdf_path = Path("sample.pdf")

pdf_bytes = pdf_path.read_bytes()
text = extract_pdf_text(pdf_bytes)

print("Extracted PDF text:")
print(text)