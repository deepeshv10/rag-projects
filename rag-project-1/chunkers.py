"""
Three chunking strategies to compare:
  1. fixed    — baseline character-window (same as src/rag/)
  2. sentence — groups whole sentences up to a size limit
  3. recursive — splits by paragraph first, then by sentence
"""

import nltk

nltk.download("punkt_tab", quiet=True)

from nltk.tokenize import sent_tokenize

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


# ---------------------------------------------------------------------------
# Strategy 1: Fixed-window (baseline)
# ---------------------------------------------------------------------------

def chunk_fixed(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into fixed-size character windows with overlap."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


# ---------------------------------------------------------------------------
# Strategy 2: Sentence-aware
# ---------------------------------------------------------------------------

def chunk_sentences(text: str, max_chunk_size: int = CHUNK_SIZE) -> list[str]:
    """Group consecutive sentences until the chunk approaches max_chunk_size."""
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk: list[str] = []
    current_len = 0

    for sentence in sentences:
        sentence_len = len(sentence)

        if current_len + sentence_len > max_chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_len = 0

        current_chunk.append(sentence)
        current_len += sentence_len + 1  # +1 for the joining space

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


# ---------------------------------------------------------------------------
# Strategy 3: Recursive (paragraph → sentence → character)
# ---------------------------------------------------------------------------

def chunk_recursive(text: str, max_chunk_size: int = CHUNK_SIZE) -> list[str]:
    """Split by paragraph first; if a paragraph is too long, split by sentence;
    if a sentence is still too long, fall back to fixed-window."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []

    for para in paragraphs:
        if len(para) <= max_chunk_size:
            chunks.append(para)
        else:
            # paragraph too long — break into sentence groups
            sentence_chunks = chunk_sentences(para, max_chunk_size)
            for sc in sentence_chunks:
                if len(sc) <= max_chunk_size:
                    chunks.append(sc)
                else:
                    # single sentence too long — fall back to fixed window
                    chunks.extend(chunk_fixed(sc, max_chunk_size))

    return chunks


# ---------------------------------------------------------------------------
# Registry — easy lookup by name
# ---------------------------------------------------------------------------

STRATEGIES = {
    "fixed": chunk_fixed,
    "sentence": chunk_sentences,
    "recursive": chunk_recursive,
}
