"""News deduplication service."""

import hashlib
import difflib
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session

from app.database import NewsArticleDB, StoryDB, NewsSourceDB
from app.logger import setup_logger

logger = setup_logger(__name__)


class Deduplicator:
    """Deduplicates articles and groups them into stories."""
    
    def __init__(self, db: Session):
        """Initialize deduplicator."""
        self.db = db
        self.similarity_threshold = 0.75  # 75% similarity to consider as duplicate
    
    def deduplicate(self, hours: int = 24) -> dict:
        """
        Deduplicate articles and create/update stories.
        
        Args:
            hours: Look back this many hours for deduplication
            
        Returns:
            Dictionary with deduplication statistics
        """
        stats = {
            "articles_processed": 0,
            "stories_created": 0,
            "stories_updated": 0,
            "duplicates_found": 0
        }
        
        # Get articles from last N hours that haven't been processed
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        articles = self.db.query(NewsArticleDB).filter(
            NewsArticleDB.retrieved_at >= cutoff_time
        ).all()
        
        logger.info(f"Processing {len(articles)} articles for deduplication...")
        
        processed_urls = set()
        
        for article in articles:
            if article.url in processed_urls:
                continue
            
            # Find similar articles
            similar = self._find_similar_articles(article, articles)
            
            # Generate story ID to check if it exists
            story_id = f"story-{hashlib.md5(article.title.encode()).hexdigest()[:8]}"
            existing = self.db.query(StoryDB).filter(StoryDB.id == story_id).first()
            
            # Create or update story
            self._get_or_create_story(article, similar)
            
            # Track articles processed
            stats["articles_processed"] += len(similar)
            
            # Track duplicates
            if len(similar) > 1:
                stats["duplicates_found"] += len(similar) - 1
            
            # Track story creation vs update
            if existing:
                stats["stories_updated"] += 1
            else:
                stats["stories_created"] += 1
            
            # Mark all similar articles as processed
            for dup in similar:
                processed_urls.add(dup.url)
        
        logger.info(
            f"\n✓ Deduplication Summary:"
            f"\n  Articles processed: {stats['articles_processed']}"
            f"\n  Stories created: {stats['stories_created']}"
            f"\n  Stories updated: {stats['stories_updated']}"
            f"\n  Duplicates found: {stats['duplicates_found']}"
        )
        
        return stats
    
    def _find_similar_articles(
        self, 
        article: NewsArticleDB, 
        all_articles: List[NewsArticleDB]
    ) -> List[NewsArticleDB]:
        """Find articles similar to the given one."""
        similar = [article]
        
        # Fast path: content hash match
        if article.content_hash:
            hash_matches = [
                a for a in all_articles 
                if a.content_hash == article.content_hash and a.url != article.url
            ]
            if hash_matches:
                return similar + hash_matches
        
        # Fallback: title similarity
        for other in all_articles:
            if other.url == article.url:
                continue
            
            # Check if titles are similar enough
            similarity = difflib.SequenceMatcher(
                None,
                article.title.lower(),
                other.title.lower()
            ).ratio()
            
            if similarity >= self.similarity_threshold:
                # Also check publication date is close
                if self._dates_are_close(article.published_at, other.published_at):
                    similar.append(other)
        
        return similar
    
    @staticmethod
    def _dates_are_close(
        date1: Optional[datetime], 
        date2: Optional[datetime], 
        hours: int = 24
    ) -> bool:
        """Check if two dates are within N hours of each other."""
        if not date1 or not date2:
            return True  # Accept if dates are missing
        
        diff = abs((date1 - date2).total_seconds())
        return diff <= hours * 3600
    
    def _get_or_create_story(
        self, 
        primary_article: NewsArticleDB, 
        similar_articles: List[NewsArticleDB]
    ) -> str:
        """Create or update a story from similar articles."""
        
        # Generate story ID
        story_id = f"story-{hashlib.md5(primary_article.title.encode()).hexdigest()[:8]}"
        
        # Check if story exists
        existing_story = self.db.query(StoryDB).filter(
            StoryDB.id == story_id
        ).first()
        
        if existing_story:
            # Update existing story
            existing_story.source_count = len(similar_articles)
            existing_story.updated_at = datetime.utcnow()
            existing_story.status = "NEW"  # Reset to NEW if was something else
            self.db.commit()
            
            # Add sources if not already present
            for article in similar_articles:
                self._add_source_if_not_exists(story_id, article)
        else:
            # Create new story
            story = StoryDB(
                id=story_id,
                title=primary_article.title,
                summary=primary_article.summary,
                status="NEW",
                source_count=len(similar_articles),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.db.add(story)
            self.db.commit()
            
            # Add sources
            for article in similar_articles:
                self._add_source_if_not_exists(story_id, article)
        
        return story_id
    
    def _add_source_if_not_exists(self, story_id: str, article: NewsArticleDB) -> None:
        """Add article as a source for story if not already added."""
        
        source_id = f"src-{hashlib.md5(f'{story_id}{article.url}'.encode()).hexdigest()[:8]}"
        
        existing = self.db.query(NewsSourceDB).filter(
            NewsSourceDB.id == source_id
        ).first()
        
        if not existing:
            source = NewsSourceDB(
                id=source_id,
                story_id=story_id,
                article_id=article.id,
                source_name=article.source,
                url=article.url,
                published_at=article.published_at,
                reliability_score=0.7  # Default reliability
            )
            self.db.add(source)
            self.db.commit()
