# backend/utils/text_chunk.py
import re
from typing import List, Iterable, Tuple

HEADER_RE = re.compile(r"^\s*(#{1,6}\s+|[A-Z0-9][\w\s\-:]{0,60}$|(\d+(\.\d+){0,3})\s+)", re.M)
PAGE_BREAK_RE = re.compile(r"\f")  # PDF extractors often add \f for page breaks

def _split_paragraphs(text: str) -> List[str]:
    # collapse many newlines but preserve blank lines as paragraph breaks
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text.split("\n\n")

def _attach_headers(paragraphs: List[str]) -> List[str]:
    """If a paragraph looks like a header, attach it to the following paragraph."""
    out = []
    i = 0
    while i < len(paragraphs):
        cur = paragraphs[i].strip()
        if i + 1 < len(paragraphs) and HEADER_RE.match(cur):
            # attach header to next paragraph
            nxt = paragraphs[i + 1].strip()
            out.append(cur + "\n\n" + nxt)
            i += 2
        else:
            out.append(cur)
            i += 1
    return out

def split_text(text: str, max_chars: int = 3000, overlap: int = 300) -> List[str]:
    """Header-aware, paragraph-first splitter with soft page boundaries."""
    # Prefer to split on pages first if present
    pages = PAGE_BREAK_RE.split(text) if "\f" in text else [text]
    chunks: List[str] = []
    for page in pages:
        paras = _attach_headers(_split_paragraphs(page))
        cur = ""
        for p in paras:
            if not cur:
                cur = p
                continue
            if len(cur) + len(p) + 2 <= max_chars:
                cur += "\n\n" + p
            else:
                # emit cur; start new, with overlap from the tail
                if cur:
                    chunks.append(cur)
                # overlap: carry last `overlap` chars of previous chunk as context
                tail = cur[-overlap:] if overlap and len(cur) > overlap else ""
                cur = (tail + "\n\n" + p).strip() if tail else p
        if cur:
            chunks.append(cur)
    return [c.strip() for c in chunks if c.strip()]
