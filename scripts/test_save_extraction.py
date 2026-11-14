
from pathlib import Path

from app.pdf_extractor import extract_pages
from app.chunking import build_chunks
from app.extraction import (
    extract_contract_data,
    consolidate_extraction,
)
from app.repo import save_contract, save_analysis_result


# 1. PDF input
pdf_path = Path("tests/samples/sample.pdf")

if not pdf_path.exists():
    raise FileNotFoundError(f"PDF not found: {pdf_path}")


# 2. Extract PDF pages
pages = extract_pages(str(pdf_path))

if not pages:
    raise ValueError("No pages were extracted from the PDF.")

print(f"Pages extracted: {len(pages)}")


# 3. Generate chunks
chunks = build_chunks(pages)

print(f"Chunks generated: {len(chunks)}")


# 4. Save contract and obtain its UUID
contract_id = save_contract(
    filename=pdf_path.name,
    pages=pages,
    chunks=chunks,
)

print(f"Contract saved: {contract_id}")


# 5. Extract structured data page by page
page_results = []

for page in pages:
    text = page["text"].strip()

    if not text:
        print(f"Skipping empty page: {page['page']}")
        continue

    result = extract_contract_data(
        text=text,
        page_number=page["page"],
    )

    page_results.append(result)

    print(f"Page {page['page']} extracted successfully.")


# 6. Consolidate page-level results
if not page_results:
    raise ValueError("No structured extraction results were generated.")

final_result = consolidate_extraction(page_results)

print("\nContract-level extraction completed.")


# 7. Save consolidated result in Supabase
result_id = save_analysis_result(
    contract_id=contract_id,
    analysis_type="metadata_extraction",
    result=final_result,
)


# 8. Display results
print("\n========== EXTRACTION SUMMARY ==========")
print(f"Contract ID: {contract_id}")
print(f"Analysis ID: {result_id}")
print(f"Pages processed: {len(page_results)}")
print(f"Clauses extracted: {len(final_result.clauses)}")
print(f"Parties identified: {len(final_result.metadata.parties)}")

print("\n========== CONSOLIDATED RESULT ==========")
print(final_result.model_dump_json(indent=2))
