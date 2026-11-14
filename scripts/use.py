from app.pdf_extractor import extract_pages
pages = extract_pages("tests/samples/your_contract.pdf")
print(type(pages[0]))
print(pages[0].keys())