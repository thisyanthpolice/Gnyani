"""
SQLAlchemy ORM models — auto-created on startup.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Website(Base):
    """Tracks every website submitted for training."""
    __tablename__ = "websites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(2048), nullable=False)
    status = Column(String(50), default="pending")  # pending | crawling | embedding | ready | failed
    page_count = Column(Integer, default=0)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    documents = relationship("Document", back_populates="website", cascade="all, delete-orphan")
    chats = relationship("Chat", back_populates="website", cascade="all, delete-orphan")


class Document(Base):
    """Individual pages/chunks extracted from a website."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)
    url = Column(String(2048), nullable=False)
    title = Column(String(500), nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    website = relationship("Website", back_populates="documents")


class Chat(Base):
    """Chat log — every question + answer pair."""
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)  # list of source URLs
    created_at = Column(DateTime, default=datetime.utcnow)

    website = relationship("Website", back_populates="chats")
