from app.pdf_extractor import extract_pages      # your Phase 1 function
from app.chunking import build_chunks

chunks = build_chunks(extract_pages("tests/samples/sample.pdf"))
sizes = [len(c.text) for c in chunks]
print(len(chunks), min(sizes), max(sizes), sum(sizes) // len(sizes))
for c in chunks[:8]:
    print(c.chunk_id, c.page, c.section, "|", c.text[:100].replace("\n", " "))