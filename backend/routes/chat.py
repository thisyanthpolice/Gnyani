"""
Chat Route — POST /chat
========================
Accepts a question + website_id, returns RAG-grounded answer.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.db.models import Website, Chat
from backend.services.rag_pipeline import answer_query

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    question: str
    website_id: int


class ChatResponse(BaseModel):
    answer: str
    sources: List[str]


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    Ask a question about a trained website.
    Returns an LLM-generated answer grounded in the website's content.
    """
    # Validate
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # Check website exists and is ready
    website = await db.get(Website, req.website_id)
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    if website.status != "ready":
        raise HTTPException(
            status_code=400,
            detail=f"Website is not ready yet (status: {website.status}). Please wait for training to complete.",
        )

    # Run RAG pipeline
    try:
        result = answer_query(req.question, req.website_id)
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate answer: {str(e)}")

    # Log chat to database
    chat_log = Chat(
        website_id=req.website_id,
        question=req.question,
        answer=result["answer"],
        sources=result["sources"],
    )
    db.add(chat_log)
    await db.commit()

    return ChatResponse(answer=result["answer"], sources=result["sources"])
