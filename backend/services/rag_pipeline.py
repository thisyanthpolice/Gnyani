"""
RAG Pipeline
==============
Orchestrates: query embedding → FAISS search → LLM answer generation.

Uses GPT-4o-mini for cost-efficient, grounded answers.
"""

import logging
import hashlib
import json
from typing import Dict, Optional
from openai import OpenAI

from backend.config import settings
from backend.services.embeddings import embed_query
from backend.services.vector_store import VectorStore

logger = logging.getLogger(__name__)

# ── OpenAI client (uses same key from .env) ──
client = OpenAI(api_key=settings.OPENAI_API_KEY)

# ── Redis cache (optional) ──
_redis_client = None

def _get_redis():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    if settings.REDIS_URL:
        try:
            import redis
            _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            _redis_client.ping()
            logger.info("Redis cache connected")
            return _redis_client
        except Exception as e:
            logger.warning(f"Redis not available: {e}")
    return None


def _cache_key(website_id: int, question: str) -> str:
    h = hashlib.md5(f"{website_id}:{question.lower().strip()}".encode()).hexdigest()
    return f"rag:cache:{h}"


def _get_cached(website_id: int, question: str) -> Optional[Dict]:
    r = _get_redis()
    if r is None:
        return None
    try:
        data = r.get(_cache_key(website_id, question))
        if data:
            logger.info("Cache hit")
            return json.loads(data)
    except Exception:
        pass
    return None


def _set_cached(website_id: int, question: str, result: Dict):
    r = _get_redis()
    if r is None:
        return
    try:
        r.setex(_cache_key(website_id, question), 3600, json.dumps(result))
    except Exception:
        pass


# ── System prompt template ──
SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on website content.

Answer ONLY using the context provided below.
If the answer is not present in the context, say "I don't have enough information from the website to answer that question."
Be concise and accurate. Cite the source URLs when relevant."""

USER_PROMPT_TEMPLATE = """Context:
{context}

Question: {question}

Provide a clear, accurate answer based only on the context above."""


def answer_query(question: str, website_id: int, top_k: int = 5) -> Dict:
    """
    Full RAG pipeline: embed question → search → LLM answer.

    Args:
        question:   User's question
        website_id: Which website's knowledge base to search
        top_k:      Number of chunks to retrieve

    Returns:
        {"answer": "...", "sources": ["url1", "url2"]}
    """
    # Check cache first
    cached = _get_cached(website_id, question)
    if cached:
        return cached

    # 1. Load the vector store
    store = VectorStore(website_id)
    if not store.load():
        return {
            "answer": "This website hasn't been trained yet. Please train it first.",
            "sources": [],
        }

    # 2. Embed the question
    query_vector = embed_query(question)

    # 3. Search FAISS for relevant chunks
    results = store.search(query_vector, top_k=top_k)

    if not results:
        return {
            "answer": "I couldn't find any relevant information on the website.",
            "sources": [],
        }

    # 4. Build context from top chunks
    context_parts = []
    source_urls = []
    for i, r in enumerate(results):
        context_parts.append(f"[Source {i+1}: {r['url']}]\n{r['text']}")
        if r["url"] not in source_urls:
            source_urls.append(r["url"])

    context = "\n\n---\n\n".join(context_parts)

    # 5. Call LLM
    try:
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT_TEMPLATE.format(
                    context=context, question=question
                )},
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"LLM error: {e}")
        return {"answer": f"Error generating answer: {str(e)}", "sources": source_urls}

    result = {"answer": answer, "sources": source_urls}

    # Cache the result
    _set_cached(website_id, question, result)

    return result
