"""
Application configuration — loads values from .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


class Settings:
    # ── OpenAI ──────────────────────────────────────────────
    # Replace with your OpenAI API key or set in .env
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # ── PostgreSQL ──────────────────────────────────────────
    # Connection string for PostgreSQL
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/ragchatbot",
    )

    # ── Redis (optional) ────────────────────────────────────
    REDIS_URL: str = os.getenv("REDIS_URL", "")

    # ── FAISS ───────────────────────────────────────────────
    FAISS_INDEX_DIR: str = os.getenv("FAISS_INDEX_DIR", "./faiss_indexes")

    # ── Crawling defaults ───────────────────────────────────
    MAX_CRAWL_DEPTH: int = 3
    MAX_PAGES: int = 50  # safety cap

    # ── Embedding model ─────────────────────────────────────
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIM: int = 1536

    # ── LLM ─────────────────────────────────────────────────
    LLM_MODEL: str = "gpt-4o-mini"


settings = Settings()
