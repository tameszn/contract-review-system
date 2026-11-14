import pymupdf
from pathlib import Path

pdf_path=Path("tests/samples/non-pdf.docx")

if not pdf_path.exists():
    raise FileNotFoundError(f"PDF not found: {pdf_path}")

if pdf_path.suffix.lower() != ".pdf":
    raise ValueError("Provided file is not a PDF.")

with pymupdf.open(pdf_path) as document:
    print(f"Total pages: {len(document)}")

    first_page = document[0]
    text = first_page.get_text("text")

    print("\nFirst 300 characters:")
    print(text[:300])