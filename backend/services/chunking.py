"""
Text Chunking
==============
Splits long text into overlapping chunks for embedding.

Rules:
  - 300–500 words per chunk (target ~400)
  - 50-word overlap between chunks
  - Preserves sentence boundaries where possible
"""

import re
from typing import List, Dict


def _split_into_sentences(text: str) -> List[str]:
    """Split text into sentences using regex."""
    # Split on sentence-ending punctuation followed by space or end
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def chunk_text(
    text: str,
    url: str,
    chunk_size: int = 400,
    overlap: int = 50,
) -> List[Dict]:
    """
    Split text into overlapping word-based chunks.

    Args:
        text:       The full text to chunk
        url:        Source URL (attached to each chunk for traceability)
        chunk_size: Target words per chunk (300-500 range)
        overlap:    Number of overlapping words between consecutive chunks

    Returns:
        [{"text": "...", "url": "..."}]
    """
    if not text or not text.strip():
        return []

    words = text.split()

    # If text is short enough, return as single chunk
    if len(words) <= chunk_size:
        return [{"text": text.strip(), "url": url}]

    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size

        # Get the chunk words
        chunk_words = words[start:end]
        chunk_text_str = " ".join(chunk_words)

        # Try to end at a sentence boundary (look for . ! ? near the end)
        if end < len(words):
            # Search last 50 words for sentence boundary
            search_region = " ".join(chunk_words[-50:])
            last_period = max(
                search_region.rfind(". "),
                search_region.rfind("! "),
                search_region.rfind("? "),
            )
            if last_period > 0:
                # Trim chunk to sentence boundary
                trimmed = chunk_text_str[: len(chunk_text_str) - len(search_region) + last_period + 1]
                if len(trimmed.split()) >= chunk_size * 0.6:  # Don't trim too aggressively
                    chunk_text_str = trimmed

        chunks.append({
            "text": chunk_text_str.strip(),
            "url": url,
        })

        # Move forward by (chunk_size - overlap)
        step = max(chunk_size - overlap, 1)
        start += step

    return chunks


def chunk_pages(pages: List[Dict]) -> List[Dict]:
    """
    Chunk all pages — convenience wrapper.

    Args:
        pages: [{"url": "...", "title": "...", "content": "..."}]

    Returns:
        [{"text": "...", "url": "..."}]
    """
    all_chunks = []
    for page in pages:
        # Prepend title to content for context
        text = page["content"]
        if page.get("title"):
            text = f"{page['title']}. {text}"

        page_chunks = chunk_text(text, page["url"])
        all_chunks.extend(page_chunks)

    return all_chunks
