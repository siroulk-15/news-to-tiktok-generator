"""Database models and session management using SQLAlchemy."""

from datetime import datetime
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from app.config import settings
from app.logger import setup_logger

logger = setup_logger(__name__)

# Create engine
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class NewsArticleDB(Base):
    """Database model for news articles."""
    
    __tablename__ = "news_articles"
    
    id = Column(String, primary_key=True)
    source = Column(String, nullable=False)
    source_domain = Column(String, nullable=False)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    url = Column(String, nullable=False, unique=True)
    published_at = Column(DateTime, nullable=True)
    language = Column(String(10), nullable=True)
    country = Column(String(10), nullable=True)
    category = Column(String, nullable=True)
    raw_content = Column(Text, nullable=True)
    content_hash = Column(String(64), nullable=True)
    retrieved_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_source_domain', 'source_domain'),
        Index('idx_content_hash', 'content_hash'),
        Index('idx_url', 'url'),
    )


class StoryDB(Base):
    """Database model for stories (deduplicated articles)."""
    
    __tablename__ = "stories"
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="NEW")
    insolite_score = Column(Float, nullable=True)
    relevance_score = Column(Float, nullable=True)
    virality_score = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    source_count = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_status', 'status'),
        Index('idx_created_at', 'created_at'),
    )


class NewsSourceDB(Base):
    """Database model for story sources."""
    
    __tablename__ = "sources"
    
    id = Column(String, primary_key=True)
    story_id = Column(String, nullable=False)
    article_id = Column(String, nullable=False)
    source_name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    published_at = Column(DateTime, nullable=True)
    reliability_score = Column(Float, nullable=False, default=0.7)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class ScriptDraftDB(Base):
    """Database model for generated, non-published script drafts."""

    __tablename__ = "script_drafts"

    id = Column(String, primary_key=True)
    story_id = Column(String, nullable=False, unique=True)
    hook = Column(Text, nullable=False)
    context = Column(Text, nullable=False)
    call_to_action = Column(Text, nullable=False)
    draft_text = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="DRAFT")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_script_draft_status", "status"),
    )


def init_db():
    """Initialize database tables."""
    logger.info("Initializing database...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully")


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        db.close()
        logger.error(f"Error getting database session: {e}")
        raise


def close_db(db: Session):
    """Close database session."""
    if db:
        db.close()
