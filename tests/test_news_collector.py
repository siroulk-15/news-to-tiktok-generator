"""Tests for news collector service."""

from datetime import datetime
from unittest.mock import Mock

import pytest

from app.database import NewsArticleDB
from app.models import NewsArticle
from app.services.news_collector import NewsCollector
from app.sources.base import BaseNewsSource


class MockNewsSource(BaseNewsSource):
    """Mock news source for testing."""
    
    def __init__(self, name: str, articles: list = None):
        super().__init__(name)
        self.articles = articles or []
    
    def fetch(self):
        return self.articles


class TestNewsCollector:
    """Test news collector service."""
    
    def test_collector_init(self, db_session):
        """Test collector initialization."""
        collector = NewsCollector(db_session)
        
        assert collector.db is not None
    
    def test_collect_single_article(self, db_session):
        """Test collecting articles from one source."""
        # Create mock article
        article = NewsArticle(
            id="test-1",
            source="Test",
            source_domain="test.com",
            title="Test Article",
            summary="Test summary",
            url="http://test.com/1"
        )
        
        # Create mock source
        source = MockNewsSource("Test Source", [article])
        
        # Collect
        collector = NewsCollector(db_session)
        stats = collector.collect([source])
        
        assert stats["total_fetched"] == 1
        assert stats["total_stored"] == 1
        assert stats["total_duplicates"] == 0
        assert stats["by_source"]["Test Source"]["stored"] == 1
        
        # Verify article in database
        db_articles = db_session.query(NewsArticleDB).all()
        assert len(db_articles) == 1
        assert db_articles[0].title == "Test Article"
    
    def test_collect_duplicate_articles(self, db_session):
        """Test that duplicate articles are not stored twice."""
        # Create article
        article = NewsArticle(
            id="test-1",
            source="Test",
            source_domain="test.com",
            title="Test Article",
            summary="Summary",
            url="http://test.com/1"
        )
        
        # Collect from same source twice
        source = MockNewsSource("Test", [article, article])
        collector = NewsCollector(db_session)
        stats = collector.collect([source])
        
        # Should only store one
        assert stats["total_stored"] == 1
        assert stats["total_duplicates"] == 1
        
        db_articles = db_session.query(NewsArticleDB).all()
        assert len(db_articles) == 1
    
    def test_collect_multiple_sources(self, db_session):
        """Test collecting from multiple sources."""
        article1 = NewsArticle(
            id="art-1",
            source="BBC",
            source_domain="bbc.com",
            title="Article 1",
            summary="Summary 1",
            url="http://bbc.com/1"
        )
        
        article2 = NewsArticle(
            id="art-2",
            source="CNN",
            source_domain="cnn.com",
            title="Article 2",
            summary="Summary 2",
            url="http://cnn.com/1"
        )
        
        source1 = MockNewsSource("BBC", [article1])
        source2 = MockNewsSource("CNN", [article2])
        
        collector = NewsCollector(db_session)
        stats = collector.collect([source1, source2])
        
        assert stats["total_fetched"] == 2
        assert stats["total_stored"] == 2
        assert len(stats["by_source"]) == 2
        
        db_articles = db_session.query(NewsArticleDB).all()
        assert len(db_articles) == 2
    
    def test_collect_with_source_error(self, db_session):
        """Test handling of source errors."""
        # Create working source
        article = NewsArticle(
            id="test-1",
            source="Good",
            source_domain="good.com",
            title="Article",
            summary="Summary",
            url="http://good.com/1"
        )
        good_source = MockNewsSource("Good Source", [article])
        
        # Create failing source
        bad_source = MockNewsSource("Bad Source", [])
        bad_source.fetch = Mock(side_effect=Exception("Connection failed"))
        
        collector = NewsCollector(db_session)
        stats = collector.collect([good_source, bad_source])
        
        # Good source should have worked
        assert stats["total_fetched"] == 1
        assert stats["total_stored"] == 1
        
        # Error should be recorded
        assert len(stats["errors"]) == 1
        assert "Bad Source" in stats["errors"][0]
        
        # Good article should still be stored
        db_articles = db_session.query(NewsArticleDB).all()
        assert len(db_articles) == 1
    
    def test_article_exists_check(self, db_session):
        """Test article existence check."""
        # Store an article
        db_article = NewsArticleDB(
            id="test-1",
            source="Test",
            source_domain="test.com",
            title="Title",
            summary="Summary",
            url="http://test.com/1"
        )
        db_session.add(db_article)
        db_session.commit()
        
        collector = NewsCollector(db_session)
        
        # Check that URL exists
        assert collector._article_exists("http://test.com/1") is True
        
        # Check that non-existent URL doesn't
        assert collector._article_exists("http://test.com/2") is False
