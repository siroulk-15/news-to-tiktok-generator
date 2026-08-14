"""RSS feed news source implementation."""

import hashlib
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse

import feedparser

from app.models import NewsArticle
from app.sources.base import BaseNewsSource
from app.logger import setup_logger

logger = setup_logger(__name__)


class RSSNewsSource(BaseNewsSource):
    """RSS feed news source."""
    
    def __init__(self, name: str, feed_url: str, country: Optional[str] = None, language: Optional[str] = "en"):
        """
        Initialize RSS source.
        
        Args:
            name: Source name (e.g., 'BBC News')
            feed_url: URL of RSS feed
            country: Country code (optional)
            language: Language code (default: 'en')
        """
        super().__init__(name)
        self.feed_url = feed_url
        self.country = country
        self.language = language
        self.source_domain = self._extract_domain(feed_url)
    
    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract domain from URL."""
        try:
            return urlparse(url).netloc
        except Exception:
            return "unknown"
    
    def fetch(self) -> List[NewsArticle]:
        """
        Fetch articles from RSS feed.
        
        Returns:
            List of NewsArticle objects
        """
        articles = []
        
        try:
            logger.info(f"Fetching RSS feed: {self.feed_url}")
            feed = feedparser.parse(self.feed_url)
            
            if feed.bozo and feed.bozo_exception:
                logger.warning(f"RSS parsing issue for {self.name}: {feed.bozo_exception}")
            
            if not feed.entries:
                logger.warning(f"No entries found in {self.name} RSS feed")
                return articles
            
            for entry in feed.entries:
                try:
                    article = self._parse_entry(entry)
                    if article and self.validate_article(article):
                        articles.append(article)
                except Exception as e:
                    logger.warning(f"Error parsing entry from {self.name}: {e}")
                    continue
            
            logger.info(f"Successfully fetched {len(articles)} articles from {self.name}")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching RSS feed from {self.name}: {e}")
            raise
    
    def _parse_entry(self, entry) -> Optional[NewsArticle]:
        """
        Parse a single RSS entry into NewsArticle.
        
        Args:
            entry: feedparser entry object
            
        Returns:
            NewsArticle or None if parsing fails
        """
        # Extract basic fields
        title = entry.get("title", "").strip()
        url = entry.get("link", "").strip()
        summary = entry.get("summary", entry.get("description", "")).strip()
        
        # Clean HTML from summary if present
        if summary:
            summary = self._clean_html(summary)[:500]  # Limit to 500 chars
        
        if not title or not url or not summary:
            return None
        
        # Extract publication date
        published_at = None
        if entry.get("published_parsed"):
            try:
                published_at = datetime(*entry.published_parsed[:6])
            except Exception:
                pass
        
        # Generate ID
        article_id = f"{self.name.lower().replace(' ', '-')}-{hashlib.md5(url.encode()).hexdigest()[:8]}"
        
        # Generate content hash
        content_hash = hashlib.sha256(f"{title}{summary}".encode()).hexdigest()
        
        return NewsArticle(
            id=article_id,
            source=self.name,
            source_domain=self.source_domain,
            title=title,
            summary=summary,
            url=url,
            published_at=published_at,
            language=self.language,
            country=self.country,
            category=entry.get("category", "").strip() or None,
            raw_content=entry.get("content", [{}])[0].get("value") if entry.get("content") else None,
            content_hash=content_hash,
            retrieved_at=datetime.utcnow()
        )
    
    @staticmethod
    def _clean_html(text: str) -> str:
        """Remove basic HTML tags from text."""
        import re
        # Replace closing tags with space to avoid word concatenation
        text = re.sub(r"</[^>]+>", " ", text)
        # Remove opening tags
        text = re.sub(r"<[^>]+>", "", text)
        # Clean up multiple spaces
        text = re.sub(r"\s+", " ", text).strip()
        return text
