"""Phase 2: clean pages -> split each page -> attach section labels.

Input : list of {"page": int (1-based), "text": str}   (output of your Phase 1)
Output: list of Chunk
"""
import re
from collections import Counter
from typing import Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel

CHUNK_SIZE = 900
CHUNK_OVERLAP = 120
MIN_CHUNK_CHARS = 80  # smaller pieces get merged into the previous chunk


class Chunk(BaseModel):
    chunk_id: int
    page: int
    text: str
    section: Optional[str] = None


# ---------- Step 1: clean ----------

_PAGE_NUM_LINE = re.compile(r"^\s*(page\s+)?\d+\s*(of\s+\d+)?\s*$", re.IGNORECASE)


def _find_repeated_lines(pages: list[dict], min_share: float = 0.5) -> set[str]:
    """Short lines that appear on at least half the pages = headers/footers."""
    if len(pages) < 3:
        return set()
    counts: Counter = Counter()
    for p in pages:
        seen = {ln.strip() for ln in p["text"].splitlines() if 0 < len(ln.strip()) <= 80}
        counts.update(seen)
    limit = max(2, int(len(pages) * min_share))
    return {line for line, n in counts.items() if n >= limit}


def clean_pages(pages: list[dict]) -> list[dict]:
    repeated = _find_repeated_lines(pages)
    cleaned = []
    for p in pages:
        lines = [
            ln for ln in p["text"].splitlines()
            if ln.strip() not in repeated and not _PAGE_NUM_LINE.match(ln)
        ]
        text = "\n".join(lines)
        text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)      # re-join hyphenated words
        text = re.sub(r"\n(?=[a-z])", " ", text)           # line continues in lowercase -> same sentence
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        cleaned.append({"page": p["page"], "text": text})
    return cleaned


# ---------- Step 2: split each page ----------

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", "; ", " "],
)


def split_pages(pages: list[dict]) -> list[Chunk]:
    chunks: list[Chunk] = []
    for p in pages:
        if not p["text"]:
            continue
        pieces = _splitter.split_text(p["text"])
        merged: list[str] = []
        for piece in pieces:
            if merged and len(piece) < MIN_CHUNK_CHARS:
                merged[-1] += " " + piece
            else:
                merged.append(piece)
        for piece in merged:
            chunks.append(Chunk(chunk_id=len(chunks), page=p["page"], text=piece))
    return chunks


# ---------- Step 3: section labels ----------

# Matches at the START of a line only, so "$2.5 million" or "1.2.2026" don't trigger.
_HEADING = re.compile(
    r"""^\s*(
        (ARTICLE|SECTION|CLAUSE|SCHEDULE|ANNEXURE|APPENDIX)\s+[\dIVXA-Z]+[.:]?\s*[^\n]{0,60}   # ARTICLE 8 - Term
        |
        \d{1,2}(\.\d{1,2}){0,2}\.?\s+[A-Z][A-Za-z ,&/\-]{2,60}                                  # 8.2 Termination
    )""",
    re.VERBOSE | re.MULTILINE,
)


def _clean_heading(raw: str) -> Optional[str]:
    heading = raw.strip()
    return heading if heading.count(" ") < 12 else None  # long sentences aren't headings


def _heading_of(text: str) -> Optional[str]:
    m = _HEADING.search(text)
    return _clean_heading(m.group(0)) if m else None


def assign_sections(chunks: list[Chunk], default: str = "Preamble") -> list[Chunk]:
    """Chunk label = heading at the chunk's start, else the section carried over
    from earlier chunks. The carried-over section then moves to the LAST heading
    inside the chunk, so later chunks inherit the right one."""
    current = default
    for c in chunks:
        headings = [h for h in (_clean_heading(m.group(0)) for m in _HEADING.finditer(c.text)) if h]
        starts_with_heading = bool(headings) and _HEADING.match(c.text.lstrip()) is not None
        c.section = headings[0] if starts_with_heading else current
        if headings:
            current = headings[-1]
    return chunks


# ---------- Public entry point ----------

def chunk_contract(pages: list[dict]) -> list[Chunk]:
    return assign_sections(split_pages(clean_pages(pages)))