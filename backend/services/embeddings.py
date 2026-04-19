"""
Embeddings Service
===================
Generate vector embeddings using OpenAI's API.

Model: text-embedding-3-small (1536 dimensions, cost-efficient)

Prerequisites:
  - Set OPENAI_API_KEY in your .env file
  - Get your key from: https://platform.openai.com/api-keys
"""

import logging
from typing import List, Dict
import numpy as np
from openai import OpenAI

from backend.config import settings

logger = logging.getLogger(__name__)

# ── Initialize OpenAI client ────────────────────────────────
# Your API key is loaded from .env → OPENAI_API_KEY
client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Max texts per API call (OpenAI limit is 2048, we use smaller batches)
BATCH_SIZE = 100


def generate_embeddings(chunks: List[Dict]) -> List[Dict]:
    """
    Generate embeddings for a list of text chunks.

    Args:
        chunks: [{"text": "...", "url": "..."}]

    Returns:
        [{"text": "...", "url": "...", "embedding": np.array}]
    """
    if not chunks:
        return []

    results = []
    texts = [c["text"] for c in chunks]

    # Process in batches
    for i in range(0, len(texts), BATCH_SIZE):
        batch_texts = texts[i : i + BATCH_SIZE]
        batch_chunks = chunks[i : i + BATCH_SIZE]

        logger.info(f"Embedding batch {i // BATCH_SIZE + 1}: {len(batch_texts)} chunks")

        try:
            response = client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=batch_texts,
            )

            for j, embedding_data in enumerate(response.data):
                results.append({
                    "text": batch_chunks[j]["text"],
                    "url": batch_chunks[j]["url"],
                    "embedding": np.array(embedding_data.embedding, dtype=np.float32),
                })

        except Exception as e:
            logger.error(f"Embedding API error: {e}")
            raise RuntimeError(f"Failed to generate embeddings: {e}")

    logger.info(f"Generated {len(results)} embeddings")
    return results


def embed_query(question: str) -> np.ndarray:
    """
    Generate embedding for a single query string.

    Args:
        question: The user's question text

    Returns:
        numpy array of shape (1536,)
    """
    try:
        response = client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=[question],
        )
        return np.array(response.data[0].embedding, dtype=np.float32)
    except Exception as e:
        logger.error(f"Query embedding error: {e}")
        raise RuntimeError(f"Failed to embed query: {e}")
