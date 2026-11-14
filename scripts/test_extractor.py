from app.pdf_extractor import extract_pages

pages = extract_pages("tests/samples/sample.pdf")

for page in pages:
    print(f"\n--- Page {page['page_number']} ---")
    print(f"Characters: {page['character_count']}")
    print(f"Scanned/Low-text: {page['is_scanned']}")
    print(page["text"][:300])