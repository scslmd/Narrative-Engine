from __future__ import annotations

import pytest

from app.services.text_chunker import TextChunker


def test_chunker_splits_at_paragraphs():
    """Long text splits into multiple chunks, each under chunk_size limit."""
    chunk_size = 20
    chunker = TextChunker(chunk_size=chunk_size, overlap=5)

    words = list(range(100))
    text = "\n\n".join(f"{' '.join(str(w) for w in words[i:i+10])}" for i in range(0, 100, 10))

    chunks = chunker.chunk(text)

    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk.split()) <= chunk_size + 5


def test_chunker_preserves_overlap():
    """Consecutive chunks share overlapping words."""
    chunk_size = 20
    overlap = 5
    chunker = TextChunker(chunk_size=chunk_size, overlap=overlap)

    text = " ".join(str(i) for i in range(60))

    chunks = chunker.chunk(text)

    assert len(chunks) >= 2
    prev_words = chunks[0].split()
    curr_words = chunks[1].split()
    shared = prev_words[-overlap:]
    for word in shared:
        assert word in curr_words


def test_chunker_small_text_single_chunk():
    """Short text returns single chunk unchanged."""
    chunker = TextChunker(chunk_size=8000, overlap=500)
    text = "This is a short paragraph."

    chunks = chunker.chunk(text)

    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunker_respects_config():
    """Uses settings defaults (8000/500)."""
    chunker = TextChunker()

    assert chunker.chunk_size == 8000
    assert chunker.overlap == 500
