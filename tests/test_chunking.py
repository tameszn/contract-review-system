from app.chunking import _is_heading, clean_pages, build_chunks


def test_heading_detection():
    assert _is_heading("8.2 Termination")
    assert _is_heading("Section 8.2 Termination for Cause")
    assert _is_heading("ARTICLE VIII - TERMINATION")
    assert not _is_heading("$2.5 million shall be paid")
    assert not _is_heading("2.5 million units were shipped")
    assert not _is_heading("1. The Supplier shall deliver the goods within 30 days.")


def test_repeated_footer_removed():
    pages = [{"page": i, "text": f"ACME CONFIDENTIAL\nBody of page {i} is here.\nPage {i} of 4"} for i in range(1, 5)]
    out = clean_pages(pages)
    assert all("ACME CONFIDENTIAL" not in p["text"] for p in out)
    assert all("Page" not in p["text"] for p in out)
    assert "Body of page 2" in out[1]["text"]


def test_pages_and_sections_kept():
    filler = "This paragraph is ordinary contract text about the supply of goods.\n\n" * 20  # ~1,400 chars
    pages = [
        {"page": 1, "text": filler + "1. Payment Terms\n\nInvoices are payable within thirty days of receipt of invoice."},
        {"page": 2, "text": filler + "2. Termination\n\nEither party may terminate with ninety days written notice to the other."},
    ]
    chunks = build_chunks(pages)
    assert chunks[0].page == 1 and chunks[0].section == "Preamble"
    assert [c.chunk_id for c in chunks] == list(range(len(chunks)))
    assert any(c.page == 2 and c.section == "1. Payment Terms" for c in chunks)
    assert chunks[-1].page == 2 and chunks[-1].section == "2. Termination"