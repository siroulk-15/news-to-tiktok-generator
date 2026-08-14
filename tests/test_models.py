"""Tests for Pydantic models."""

from datetime import datetime

import pytest

from app.models import NewsArticle, Story, NewsSource


class TestNewsArticle:
    """Test NewsArticle model."""
    
    def test_create_news_article(self):
        """Test creating a news article."""
        article = NewsArticle(
            id="test-1",
            source="BBC",
            source_domain="bbc.com",
            title="Test Article",
            summary="This is a test",
            url="http://bbc.com/news/1"
        )
        
        assert article.id == "test-1"
        assert article.source == "BBC"
        assert article.title == "Test Article"
        assert article.url == "http://bbc.com/news/1"
    
    def test_news_article_required_fields(self):
        """Test that required fields are enforced."""
        with pytest.raises(ValueError):
            NewsArticle(
                id="test",
                source="BBC",
                source_domain="bbc.com",
                # Missing title
                summary="Summary",
                url="http://example.com"
            )
    
    def test_news_article_with_all_fields(self):
        """Test creating article with all optional fields."""
        now = datetime.utcnow()
        article = NewsArticle(
            id="test-1",
            source="BBC",
            source_domain="bbc.com",
            title="Title",
            summary="Summary",
            url="http://example.com",
            published_at=now,
            language="en",
            country="GB",
            category="news",
            raw_content="Full content",
            content_hash="abc123",
            retrieved_at=now
        )
        
        assert article.language == "en"
        assert article.country == "GB"
        assert article.category == "news"
        assert article.content_hash == "abc123"


class TestStory:
    """Test Story model."""
    
    def test_create_story(self):
        """Test creating a story."""
        story = Story(
            id="story-1",
            title="Test Story",
            summary="This is a test story"
        )
        
        assert story.id == "story-1"
        assert story.title == "Test Story"
        assert story.status == "NEW"
        assert story.source_count == 1
    
    def test_story_with_scores(self):
        """Test story with scoring."""
        story = Story(
            id="story-1",
            title="Title",
            summary="Summary",
            insolite_score=0.85,
            relevance_score=0.90,
            confidence_score=0.92
        )
        
        assert story.insolite_score == 0.85
        assert story.relevance_score == 0.90
        assert story.confidence_score == 0.92
    
    def test_story_status_values(self):
        """Test that story can have different status values."""
        statuses = ["NEW", "FILTERED", "VERIFIED", "REJECTED", "PUBLISHED"]
        
        for status in statuses:
            story = Story(
                id=f"story-{status}",
                title="Title",
                summary="Summary",
                status=status
            )
            assert story.status == status


class TestNewsSource:
    """Test NewsSource model."""
    
    def test_create_news_source(self):
        """Test creating a news source reference."""
        source = NewsSource(
            id="src-1",
            story_id="story-1",
            article_id="article-1",
            source_name="BBC",
            url="http://bbc.com/news/1"
        )
        
        assert source.id == "src-1"
        assert source.story_id == "story-1"
        assert source.source_name == "BBC"
        assert source.reliability_score == 0.7
