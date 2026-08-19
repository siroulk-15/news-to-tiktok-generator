"""Tests for RSS news source."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from app.sources.rss import RSSNewsSource
from app.models import NewsArticle
from app.cli import get_default_rss_sources


class TestRSSNewsSource:
    """Test RSS news source."""
    
    def test_init(self):
        """Test RSS source initialization."""
        source = RSSNewsSource(
            "BBC",
            "http://feeds.bbc.co.uk/news/rss.xml",
            country="GB"
        )
        
        assert source.name == "BBC"
        assert source.feed_url == "http://feeds.bbc.co.uk/news/rss.xml"
        assert source.country == "GB"
        assert source.language == "en"
        assert source.source_domain == "feeds.bbc.co.uk"

    def test_default_sources_prioritize_french_feeds(self):
        sources = get_default_rss_sources()

        assert [source.name for source in sources[:4]] == [
            "France 24",
            "RFI",
            "Franceinfo",
            "Le Monde",
        ]
        assert all(source.language == "fr" for source in sources[:4])
        assert all(source.country == "FR" for source in sources[:4])
        assert len(sources) == 7
    
    def test_extract_domain(self):
        """Test domain extraction from URL."""
        source = RSSNewsSource("Test", "http://test.com/feed")
        
        assert source._extract_domain("http://example.com/feed") == "example.com"
        assert source._extract_domain("https://sub.domain.co.uk/path") == "sub.domain.co.uk"
        assert source._extract_domain("http://localhost:8000") == "localhost:8000"
    
    def test_clean_html(self):
        """Test HTML cleaning."""
        text = "<p>Hello <b>world</b></p><a href='#'>link</a>"
        cleaned = RSSNewsSource._clean_html(text)
        
        assert cleaned == "Hello world link"
        assert "<" not in cleaned
        assert ">" not in cleaned
    
    @patch("feedparser.parse")
    def test_fetch_valid_feed(self, mock_parse):
        """Test fetching from a valid RSS feed."""
        # Mock feed data
        mock_parse.return_value = Mock(
            bozo=False,
            entries=[
                {
                    "title": "Test Article",
                    "link": "http://example.com/article1",
                    "summary": "This is a test article",
                    "published_parsed": (2026, 8, 14, 10, 30, 0, 0, 0, 0),
                    "category": "tech"
                }
            ]
        )
        
        source = RSSNewsSource("Test Source", "http://test.com/feed")
        articles = source.fetch()
        
        assert len(articles) == 1
        assert articles[0].title == "Test Article"
        assert articles[0].url == "http://example.com/article1"
        assert articles[0].summary == "This is a test article"
        assert articles[0].source == "Test Source"
    
    @patch("feedparser.parse")
    def test_fetch_empty_feed(self, mock_parse):
        """Test fetching from an empty RSS feed."""
        mock_parse.return_value = Mock(bozo=False, entries=[])
        
        source = RSSNewsSource("Test Source", "http://test.com/feed")
        articles = source.fetch()
        
        assert len(articles) == 0
    
    @patch("feedparser.parse")
    def test_fetch_with_parsing_error(self, mock_parse):
        """Test handling of parsing errors."""
        mock_parse.return_value = Mock(
            bozo=True,
            bozo_exception=Exception("Parsing error"),
            entries=[
                {
                    "title": "Article",
                    "link": "http://example.com/1",
                    "summary": "Summary",
                    "published_parsed": (2026, 8, 14, 10, 30, 0, 0, 0, 0)
                }
            ]
        )
        
        source = RSSNewsSource("Test Source", "http://test.com/feed")
        articles = source.fetch()
        
        # Should still return articles despite bozo flag
        assert len(articles) == 1
    
    @patch("feedparser.parse")
    def test_fetch_missing_required_fields(self, mock_parse):
        """Test handling of entries with missing required fields."""
        mock_parse.return_value = Mock(
            bozo=False,
            entries=[
                {
                    "title": "Article Without Link",
                    "summary": "Summary",
                    # Missing link
                },
                {
                    "title": "Article Without Summary",
                    "link": "http://example.com/2",
                    # Missing summary
                },
                {
                    "title": "Valid Article",
                    "link": "http://example.com/3",
                    "summary": "Valid summary",
                    "published_parsed": (2026, 8, 14, 10, 30, 0, 0, 0, 0)
                }
            ]
        )
        
        source = RSSNewsSource("Test Source", "http://test.com/feed")
        articles = source.fetch()
        
        # Should only return the valid article
        assert len(articles) == 1
        assert articles[0].title == "Valid Article"
    
    @patch("feedparser.parse")
    def test_validate_article(self, mock_parse):
        """Test article validation."""
        source = RSSNewsSource("Test", "http://test.com/feed")
        
        # Valid article
        valid_article = NewsArticle(
            id="test-1",
            source="Test",
            source_domain="test.com",
            title="Title",
            summary="Summary",
            url="http://example.com/1"
        )
        assert source.validate_article(valid_article) is True
        
        # Invalid articles
        invalid_article = NewsArticle(
            id="test-2",
            source="Test",
            source_domain="test.com",
            title="",  # Empty title
            summary="Summary",
            url="http://example.com/2"
        )
        assert source.validate_article(invalid_article) is False
