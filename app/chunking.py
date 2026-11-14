import re
from collections import Counter

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.schemas import Chunk

CHUNK_SIZE = 900
CHUNK_OVERLAP = 150
MIN_CHUNK_CHARS = 40

# "8.2 Termination", "8. Payment Terms", "Section 8.2 Termination"
NUMBERED_HEADING = re.compile(
    r"^\s*(?:(?:Section|Article|Clause)\s+)?\d+(?:\.\d+)*[.)]?\s+[A-Z][^\n.]{1,80}$"
)
# "ARTICLE VIII - TERMINATION", "SECTION 4: PAYMENT"
ARTICLE_HEADING = re.compile(r"^\s*(?:ARTICLE|SECTION)\s+[IVXLC\d]+\b.*$")

PAGE_NUMBER_LINE = re.compile(r"^\s*(?:page\s+)?\d+\s*(?:of\s+\d+)?\s*$", re.IGNORECASE)


def _is_heading(line: str) -> bool:
    line = line.strip()
    return bool(NUMBERED_HEADING.match(line) or ARTICLE_HEADING.match(line))

def clean_pages(pages: list[dict]) -> list[dict]:
    """pages: [{"page": 1, "text": "..."}]  ->  same shape, cleaned text."""
    # lines that appear on more than half the pages are headers/footers
    counts = Counter()
    for p in pages:
        counts.update({ln.strip() for ln in p["text"].splitlines() if ln.strip()})
    repeated = set()
    if len(pages) >= 3:
        repeated = {ln for ln, c in counts.items() if c > len(pages) / 2 and len(ln) < 80}

    cleaned = []
    for p in pages:
        lines = [
            ln for ln in p["text"].splitlines()
            if ln.strip() not in repeated and not PAGE_NUMBER_LINE.match(ln)
        ]
        text = "\n".join(lines)
        text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)   # rejoin hyphenated line breaks
        text = re.sub(r"[ \t]+", " ", text)            # collapse spaces
        text = re.sub(r"\n{3,}", "\n\n", text).strip() # keep paragraph breaks
        cleaned.append({"page": p["page"], "text": text})
    return cleaned

def split_pages(pages: list[dict]) -> list[Chunk]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks: list[Chunk] = []
    for p in pages:
        for piece in splitter.split_text(p["text"]):
            chunks.append(Chunk(chunk_id=len(chunks), page=p["page"], text=piece))
    return chunks


def assign_sections(chunks: list[Chunk]) -> list[Chunk]:
    current = "Preamble"
    for chunk in chunks:
        headings = [ln.strip() for ln in chunk.text.splitlines() if _is_heading(ln)]
        chunk.section = headings[0] if headings else current  # first heading inside, else carry over
        if headings:
            current = headings[-1]                            # next chunks inherit the last heading seen
    return chunks


def build_chunks(pages: list[dict]) -> list[Chunk]:
    chunks = assign_sections(split_pages(clean_pages(pages)))  # sections first, so tiny heading pieces still count
    chunks = [c for c in chunks if len(c.text.strip()) >= MIN_CHUNK_CHARS]
    for i, c in enumerate(chunks):
        c.chunk_id = i
    return chunks