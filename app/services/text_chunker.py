from __future__ import annotations


class TextChunker:
    def __init__(self, chunk_size: int = 8000, overlap: int = 500):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if len(text.split()) <= self.chunk_size:
            return [text]

        paragraphs = text.split("\n\n")
        chunks: list[str] = []
        current_words: list[str] = []

        for para in paragraphs:
            words = para.split()
            current_words.extend(words)

            while len(current_words) >= self.chunk_size:
                chunk_words = current_words[:self.chunk_size]
                chunks.append(" ".join(chunk_words))
                current_words = current_words[self.chunk_size - self.overlap:]

        if current_words and chunks:
            last_words = chunks[-1].split()
            if len(last_words) + len(current_words) <= self.chunk_size:
                chunks[-1] = " ".join(last_words + current_words)
            else:
                chunks.append(" ".join(current_words))
        elif current_words:
            chunks.append(" ".join(current_words))

        return chunks
