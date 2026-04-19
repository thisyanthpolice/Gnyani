"""
FastAPI Application — Entry Point
===================================
Run with:  uvicorn backend.main:app --reload --port 8000

This is the main server file that:
  1. Creates DB tables on startup
  2. Registers all API routes
  3. Configures CORS for the React frontend
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.db.database import engine
from backend.db.models import Base
from backend.routes import train, chat

# ── Logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan: create tables on startup ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ready")
    yield
    logger.info("Shutting down...")


# ── App ──
app = FastAPI(
    title="RAG Chatbot API",
    description="Train a chatbot on any website, then ask questions.",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS (allow React frontend on localhost:5173) ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",   # Alternative
        "http://127.0.0.1:5173",
        "*",                       # For development — restrict in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routes ──
app.include_router(train.router, tags=["Training"])
app.include_router(chat.router, tags=["Chat"])


@app.get("/")
async def root():
    return {
        "service": "RAG Chatbot API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "train": "POST /train",
            "status": "GET /status/{website_id}",
            "chat": "POST /chat",
            "websites": "GET /websites",
        },
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
