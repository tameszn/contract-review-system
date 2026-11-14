from pathlib import Path
import pymupdf


def extract_pages(pdf_path: str) -> list[dict]:
    """
    Extract text from every PDF page.

    Returns:
        List of dictionaries containing:
        - page_number: 1-based page number
        - text: extracted page text
        - character_count: number of extracted characters
        - is_scanned: whether the page likely contains no extractable text
    """

    pdf_path = Path("tests/samples/sample.pdf")

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if not pdf_path.is_file() or pdf_path.suffix.lower() != ".pdf":
        raise ValueError("Provided path must point to a PDF file.")

    extracted_pages = []

    try:
        with pymupdf.open(pdf_path) as document:

            if document.is_encrypted:
                raise ValueError("Encrypted PDFs are not supported.")

            for page_index, page in enumerate(document):

                text = page.get_text("text").strip()

                extracted_pages.append({
                    "page_number": page_index + 1,
                    "text": text,
                    "character_count": len(text),
                    "is_scanned": len(text) < 20
                })

    except pymupdf.FileDataError as error:
        raise ValueError(f"Invalid or corrupted PDF: {error}") from error

    return extracted_pages


pages = extract_pages("sample.pdf")

for page in pages:
    print(f"\n--- Page {page['page_number']} ---")
    print(f"Characters: {page['character_count']}")
    print(f"Scanned/Low-text: {page['is_scanned']}")
    print(page["text"][:300])