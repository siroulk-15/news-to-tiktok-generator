"""Pydantic models for data validation and serialization."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class NewsArticle(BaseModel):
    """Represents a single news article from any source."""
    
    id: str = Field(..., description="Unique identifier")
    source: str = Field(..., description="Source name (e.g., 'BBC', 'Reuters')")
    source_domain: str = Field(..., description="Domain of the source")
    title: str = Field(..., description="Article title")
    summary: str = Field(..., description="Article summary/description")
    url: str = Field(..., description="URL to the article")
    published_at: Optional[datetime] = Field(None, description="Publication date")
    language: Optional[str] = Field(None, description="Article language (ISO 639-1)")
    country: Optional[str] = Field(None, description="Country code (ISO 3166-1)")
    category: Optional[str] = Field(None, description="Category/topic")
    raw_content: Optional[str] = Field(None, description="Full article content")
    content_hash: Optional[str] = Field(None, description="SHA256 hash of content for deduplication")
    retrieved_at: datetime = Field(default_factory=datetime.utcnow, description="When article was retrieved")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "rss-bbc-001",
                "source": "BBC",
                "source_domain": "bbc.com",
                "title": "Unusual event occurs",
                "summary": "A strange incident happened today",
                "url": "https://bbc.com/news/article",
                "published_at": "2026-08-14T10:30:00",
                "language": "en",
                "country": "GB",
                "category": "unusual-events",
                "retrieved_at": "2026-08-14T15:00:00",
            }
        }


class Story(BaseModel):
    """Represents a deduplicated story (may have multiple sources)."""
    
    id: str = Field(..., description="Unique story ID")
    title: str = Field(..., description="Story title")
    summary: str = Field(..., description="Story summary")
    status: str = Field(default="NEW", description="Story status")
    insolite_score: Optional[float] = Field(None, description="Insolite score (0-1)")
    relevance_score: Optional[float] = Field(None, description="Relevance score (0-1)")
    virality_score: Optional[float] = Field(None, description="Virality potential (0-1)")
    confidence_score: Optional[float] = Field(None, description="Confidence score (0-1)")
    source_count: int = Field(default=1, description="Number of sources for this story")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "story-001",
                "title": "Unusual event occurs",
                "summary": "A strange incident happened today",
                "status": "NEW",
                "insolite_score": 0.85,
                "relevance_score": 0.90,
                "virality_score": 0.75,
                "confidence_score": 0.92,
                "source_count": 3,
            }
        }


class NewsSource(BaseModel):
    """Reference to a source for a story."""
    
    id: str = Field(..., description="Unique ID")
    story_id: str = Field(..., description="Associated story ID")
    article_id: str = Field(..., description="Associated article ID")
    source_name: str = Field(..., description="Source name")
    url: str = Field(..., description="Article URL")
    published_at: Optional[datetime] = Field(None)
    reliability_score: float = Field(default=0.7, description="Source reliability (0-1)")
