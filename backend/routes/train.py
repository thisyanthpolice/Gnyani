"""
Train Route — POST /train, GET /status/{website_id}
=====================================================
Accepts a URL, runs the full training pipeline as a background task.
"""

import logging
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db.database import get_db
from backend.db.models import Website, Document
from backend.services.crawler import crawl_website
from backend.services.chunking import chunk_pages
from backend.services.embeddings import generate_embeddings
from backend.services.vector_store import VectorStore

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Request / Response schemas ──

class TrainRequest(BaseModel):
    url: str  # The website URL to train on


class TrainResponse(BaseModel):
    website_id: int
    status: str
    message: str


class StatusResponse(BaseModel):
    website_id: int
    url: str
    status: str
    page_count: int
    error: str | None = None


# ── Background training task ──

async def _run_training(website_id: int, url: str):
    """
    Full pipeline: crawl → chunk → embed → store.
    Runs as a background task so the API responds immediately.
    """
    from backend.db.database import async_session

    async with async_session() as db:
        try:
            # Update status → crawling
            website = await db.get(Website, website_id)
            website.status = "crawling"
            await db.commit()

            # 1. Crawl
            logger.info(f"[Train] Crawling {url}...")
            pages = crawl_website(url)

            if not pages:
                website.status = "failed"
                website.error = "No content found on the website"
                await db.commit()
                return

            website.page_count = len(pages)
            await db.commit()

            # Save documents to DB
            for page in pages:
                doc = Document(
                    website_id=website_id,
                    url=page["url"],
                    title=page.get("title", ""),
                    content=page["content"],
                )
                db.add(doc)
            await db.commit()

            # 2. Chunk
            logger.info(f"[Train] Chunking {len(pages)} pages...")
            chunks = chunk_pages(pages)
            logger.info(f"[Train] Created {len(chunks)} chunks")

            # 3. Embed
            website.status = "embedding"
            await db.commit()

            logger.info(f"[Train] Generating embeddings...")
            embedded_chunks = generate_embeddings(chunks)

            # 4. Store in FAISS
            store = VectorStore(website_id)
            store.create_index()
            store.add_embeddings(embedded_chunks)
            store.save()

            # Done
            website.status = "ready"
            website.error = None
            await db.commit()
            logger.info(f"[Train] Website {website_id} training complete!")

        except Exception as e:
            logger.error(f"[Train] Failed: {e}", exc_info=True)
            website = await db.get(Website, website_id)
            if website:
                website.status = "failed"
                website.error = str(e)[:500]
                await db.commit()


# ── Endpoints ──

@router.post("/train", response_model=TrainResponse)
async def train_website(
    req: TrainRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a website URL for training.
    The crawling + embedding runs in the background.
    """
    # Validate URL
    url = req.url.strip().rstrip("/")
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")

    # Create website record
    website = Website(url=url, status="pending")
    db.add(website)
    await db.commit()
    await db.refresh(website)

    # Kick off background training
    background_tasks.add_task(_run_training, website.id, url)

    return TrainResponse(
        website_id=website.id,
        status="pending",
        message=f"Training started for {url}. Use /status/{website.id} to check progress.",
    )


@router.get("/status/{website_id}", response_model=StatusResponse)
async def get_status(website_id: int, db: AsyncSession = Depends(get_db)):
    """Check the training status of a website."""
    website = await db.get(Website, website_id)
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    return StatusResponse(
        website_id=website.id,
        url=website.url,
        status=website.status,
        page_count=website.page_count or 0,
        error=website.error,
    )


@router.get("/websites")
async def list_websites(db: AsyncSession = Depends(get_db)):
    """List all trained websites."""
    result = await db.execute(select(Website).order_by(Website.created_at.desc()))
    websites = result.scalars().all()
    return [
        {
            "id": w.id,
            "url": w.url,
            "status": w.status,
            "page_count": w.page_count or 0,
            "created_at": w.created_at.isoformat() if w.created_at else None,
        }
        for w in websites
    ]
