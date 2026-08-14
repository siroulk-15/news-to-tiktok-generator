"""News collection service."""

from typing import List
from sqlalchemy.orm import Session

from app.models import NewsArticle
from app.sources.base import BaseNewsSource
from app.database import NewsArticleDB
from app.logger import setup_logger

logger = setup_logger(__name__)


class NewsCollector:
    """Collects news from multiple sources and stores them."""
    
    def __init__(self, db: Session):
        """Initialize collector."""
        self.db = db
    
    def collect(self, sources: List[BaseNewsSource]) -> dict:
        """
        Collect news from all sources.
        
        Args:
            sources: List of news sources to collect from
            
        Returns:
            Dictionary with collection statistics
        """
        stats = {
            "total_fetched": 0,
            "total_stored": 0,
            "total_duplicates": 0,
            "errors": [],
            "by_source": {}
        }
        
        for source in sources:
            try:
                logger.info(f"Collecting from {source.name}...")
                articles = source.fetch()
                
                stored_count = 0
                duplicate_count = 0
                
                for article in articles:
                    if self._article_exists(article.url):
                        duplicate_count += 1
                        continue
                    
                    try:
                        self._store_article(article)
                        stored_count += 1
                    except Exception as e:
                        logger.error(f"Error storing article from {source.name}: {e}")
                        stats["errors"].append(str(e))
                
                stats["total_fetched"] += len(articles)
                stats["total_stored"] += stored_count
                stats["total_duplicates"] += duplicate_count
                stats["by_source"][source.name] = {
                    "fetched": len(articles),
                    "stored": stored_count,
                    "duplicates": duplicate_count
                }
                
                logger.info(
                    f"✓ {source.name}: fetched={len(articles)}, "
                    f"stored={stored_count}, duplicates={duplicate_count}"
                )
                
            except Exception as e:
                logger.error(f"✗ Error collecting from {source.name}: {e}")
                stats["errors"].append(f"{source.name}: {str(e)}")
        
        logger.info(
            f"\n📊 Collection Summary:"
            f"\n  Total fetched: {stats['total_fetched']}"
            f"\n  Total stored: {stats['total_stored']}"
            f"\n  Duplicates: {stats['total_duplicates']}"
        )
        
        return stats
    
    def _article_exists(self, url: str) -> bool:
        """Check if article with given URL already exists."""
        return self.db.query(NewsArticleDB).filter(
            NewsArticleDB.url == url
        ).first() is not None
    
    def _store_article(self, article: NewsArticle) -> None:
        """Store article in database."""
        db_article = NewsArticleDB(
            id=article.id,
            source=article.source,
            source_domain=article.source_domain,
            title=article.title,
            summary=article.summary,
            url=article.url,
            published_at=article.published_at,
            language=article.language,
            country=article.country,
            category=article.category,
            raw_content=article.raw_content,
            content_hash=article.content_hash,
            retrieved_at=article.retrieved_at
        )
        self.db.add(db_article)
        self.db.commit()
