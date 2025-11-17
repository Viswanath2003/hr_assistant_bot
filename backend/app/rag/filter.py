import re
from typing import List, Tuple, Dict

TITLE_KEYWORDS = [
    "holiday calendar", "mandate holidays", "optional holidays",
    "holiday calendar 2025", "holiday calendar 2024", "holiday calendar 2023",
    "sigmoid", "company", "address", "email", "web:", "web", "phone", "ph:"
]

UPPERCASE_RATIO_THRESHOLD = 0.6
MIN_CHUNK_LEN = 2  # characters
MAX_TITLE_WORDS = 6  # if a small chunk has a few words and all uppercase -> title/header
MAX_TITLE_CHARS = 120  # only consider a chunk a title if it's short


def _uppercase_ratio(s: str) -> float:
    letters = [c for c in s if c.isalpha()]
    if not letters:
        return 0.0
    up = sum(1 for c in letters if c.isupper())
    return up / len(letters)


def _normalize_text(s: str) -> str:
    """
    Normalize text for duplicate detection: lower, collapse whitespace.
    """
    return re.sub(r"\s+", " ", s.strip().lower())


def looks_like_title(s: str) -> bool:
    """
    Heuristic to decide if a small piece of text is just a header/title.
    """
    txt = s.strip()
    if not txt:
        return True
    lower = txt.lower()

    # Only treat as a title/header if the chunk is reasonably short.
    # Long page-level chunks often contain titles plus useful content
    # (e.g., a page that starts with 'Holiday Calendar' and then lists holidays),
    # so we avoid classifying long chunks as titles to prevent dropping them entirely.
    if len(txt) <= MAX_TITLE_CHARS:
        # common title lines (only for short chunks)
        for kw in TITLE_KEYWORDS:
            if kw in lower:
                return True

        # mostly uppercase and short -> likely a heading
        if len(txt.split()) <= MAX_TITLE_WORDS and _uppercase_ratio(txt) > UPPERCASE_RATIO_THRESHOLD:
            return True

        # lines with many punctuation but little alpha
        if len(re.findall(r"[A-Za-z]", txt)) < 3 and len(txt) < 40:
            return True

    # otherwise assume not a title/header
    return False


def is_noise_chunk(text: str) -> bool:
    """
    Lightweight wrapper: consider titles, extremely short lines, or whitespace-only as noise.
    """
    if not text or len(text.strip()) <= MIN_CHUNK_LEN:
        return True
    if looks_like_title(text):
        return True
    return False


def filter_chunks(chunks: List[str], metadatas: List[Dict]) -> Tuple[List[str], List[Dict]]:
    """
    Remove chunks detected as noise and exact-duplicate chunks (normalized).
    Returns (filtered_chunks, filtered_metadatas).
    
    IMPORTANT: Preserves original chunk_index metadata - does NOT reindex!
    This is crucial for maintaining chunk identity across pipeline.
    """
    assert len(chunks) == len(metadatas), "chunks/metadatas length mismatch"

    new_chunks = []
    new_metas = []
    seen = set()

    for chunk, meta in zip(chunks, metadatas):
        norm = _normalize_text(chunk)
        if norm in seen:
            # duplicate content across chunks -> skip
            continue

        if not is_noise_chunk(chunk):
            seen.add(norm)
            meta = dict(meta)  # copy
            meta["filtered"] = False
            # PRESERVE ORIGINAL chunk_index - DO NOT REINDEX
            # Original chunk_index from metadata is kept as-is
            new_chunks.append(chunk.strip())
            new_metas.append(meta)
        else:
            # skip noise chunks
            continue
    return new_chunks, new_metas