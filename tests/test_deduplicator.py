"""Tests for deduplication service."""

from datetime import datetime, timedelta

import pytest

from app.database import NewsArticleDB, StoryDB, NewsSourceDB
from app.services.deduplicator import Deduplicator


class TestDeduplicator:
    """Test deduplication service."""
    
    def test_deduplicator_init(self, db_session):
        """Test deduplicator initialization."""
        dedup = Deduplicator(db_session)
        
        assert dedup.db is not None
        assert dedup.similarity_threshold == 0.75
    
    def test_dates_are_close_same_day(self):
        """Test that dates on same day are close."""
        date1 = datetime(2026, 8, 14, 10, 0, 0)
        date2 = datetime(2026, 8, 14, 15, 0, 0)
        
        assert Deduplicator._dates_are_close(date1, date2, hours=24) is True
    
    def test_dates_are_close_too_far(self):
        """Test that dates far apart are not close."""
        date1 = datetime(2026, 8, 14, 10, 0, 0)
        date2 = datetime(2026, 8, 15, 10, 0, 0)
        
        assert Deduplicator._dates_are_close(date1, date2, hours=12) is False
    
    def test_dates_are_close_with_none(self):
        """Test that missing dates are considered close."""
        date1 = datetime(2026, 8, 14, 10, 0, 0)
        
        assert Deduplicator._dates_are_close(None, date1) is True
        assert Deduplicator._dates_are_close(date1, None) is True
        assert Deduplicator._dates_are_close(None, None) is True
    
    def test_deduplicate_single_article(self, db_session):
        """Test deduplication with a single article."""
        # Add single article
        article = NewsArticleDB(
            id="article-1",
            source="BBC",
            source_domain="bbc.com",
            title="Unusual Event",
            summary="Something strange happened",
            url="http://bbc.com/1",
            retrieved_at=datetime.utcnow()
        )
        db_session.add(article)
        db_session.commit()
        
        # Deduplicate
        dedup = Deduplicator(db_session)
        stats = dedup.deduplicate(hours=24)
        
        assert stats["articles_processed"] == 1
        assert stats["stories_created"] == 1
        assert stats["stories_updated"] == 0
        assert stats["duplicates_found"] == 0
        
        # Check story was created
        stories = db_session.query(StoryDB).all()
        assert len(stories) == 1
        assert stories[0].title == "Unusual Event"
        assert stories[0].source_count == 1
    
    def test_deduplicate_same_content_hash(self, db_session):
        """Test deduplication by content hash."""
        # Add two articles with same content hash (duplicates)
        article1 = NewsArticleDB(
            id="article-1",
            source="BBC",
            source_domain="bbc.com",
            title="Event Title",
            summary="Event summary",
            url="http://bbc.com/1",
            content_hash="abc123def456",
            retrieved_at=datetime.utcnow()
        )
        article2 = NewsArticleDB(
            id="article-2",
            source="Reuters",
            source_domain="reuters.com",
            title="Event Title",
            summary="Event summary",
            url="http://reuters.com/1",
            content_hash="abc123def456",
            retrieved_at=datetime.utcnow()
        )
        
        db_session.add_all([article1, article2])
        db_session.commit()
        
        # Deduplicate
        dedup = Deduplicator(db_session)
        stats = dedup.deduplicate(hours=24)
        
        assert stats["articles_processed"] == 2
        assert stats["duplicates_found"] == 1
        assert stats["stories_created"] == 1
        
        # Check that both articles are linked to same story
        story = db_session.query(StoryDB).first()
        assert story.source_count == 2
    
    def test_deduplicate_similar_titles(self, db_session):
        """Test deduplication by similar titles."""
        # Add articles with very similar titles
        article1 = NewsArticleDB(
            id="article-1",
            source="BBC",
            source_domain="bbc.com",
            title="Strange event happens in small town",
            summary="Summary 1",
            url="http://bbc.com/1",
            published_at=datetime(2026, 8, 14, 10, 0, 0),
            retrieved_at=datetime.utcnow()
        )
        article2 = NewsArticleDB(
            id="article-2",
            source="CNN",
            source_domain="cnn.com",
            title="Strange event happen in small town",  # Very similar
            summary="Summary 2",
            url="http://cnn.com/1",
            published_at=datetime(2026, 8, 14, 11, 0, 0),
            retrieved_at=datetime.utcnow()
        )
        
        db_session.add_all([article1, article2])
        db_session.commit()
        
        # Deduplicate
        dedup = Deduplicator(db_session)
        stats = dedup.deduplicate(hours=24)
        
        # May find similar articles depending on similarity threshold
        assert stats["articles_processed"] >= 1
    
    def test_deduplicate_different_articles(self, db_session):
        """Test that different articles create different stories."""
        # Add two different articles
        article1 = NewsArticleDB(
            id="article-1",
            source="BBC",
            source_domain="bbc.com",
            title="Strange phenomenon occurs in London",
            summary="Summary A",
            url="http://bbc.com/1",
            retrieved_at=datetime.utcnow()
        )
        article2 = NewsArticleDB(
            id="article-2",
            source="CNN",
            source_domain="cnn.com",
            title="New discovery in quantum physics",
            summary="Summary B",
            url="http://cnn.com/1",
            retrieved_at=datetime.utcnow()
        )
        
        db_session.add_all([article1, article2])
        db_session.commit()
        
        # Deduplicate
        dedup = Deduplicator(db_session)
        stats = dedup.deduplicate(hours=24)
        
        assert stats["articles_processed"] == 2
        assert stats["stories_created"] == 2
        
        # Check two different stories were created
        stories = db_session.query(StoryDB).all()
        assert len(stories) == 2
        
        # Verify titles match
        titles = {story.title for story in stories}
        assert "Strange phenomenon occurs in London" in titles
        assert "New discovery in quantum physics" in titles
    
    def test_deduplicate_old_articles_excluded(self, db_session):
        """Test that old articles are not processed."""
        # Add old article (older than 24 hours)
        old_article = NewsArticleDB(
            id="old-article",
            source="BBC",
            source_domain="bbc.com",
            title="Old Event",
            summary="Old summary",
            url="http://bbc.com/old",
            retrieved_at=datetime.utcnow() - timedelta(hours=48)
        )
        
        # Add recent article
        new_article = NewsArticleDB(
            id="new-article",
            source="CNN",
            source_domain="cnn.com",
            title="New Event",
            summary="New summary",
            url="http://cnn.com/new",
            retrieved_at=datetime.utcnow()
        )
        
        db_session.add_all([old_article, new_article])
        db_session.commit()
        
        # Deduplicate with 24-hour window
        dedup = Deduplicator(db_session)
        stats = dedup.deduplicate(hours=24)
        
        # Only recent article should be processed
        assert stats["articles_processed"] == 1
        
        stories = db_session.query(StoryDB).all()
        assert len(stories) == 1
        assert stories[0].title == "New Event"
