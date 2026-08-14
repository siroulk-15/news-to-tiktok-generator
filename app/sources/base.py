"""Base class for news sources."""

from abc import ABC, abstractmethod
from typing import List

from app.models import NewsArticle
from app.logger import setup_logger

logger = setup_logger(__name__)


class BaseNewsSource(ABC):
    """Abstract base class for all news sources."""
    
    def __init__(self, name: str):
        """Initialize source."""
        self.name = name
    
    @abstractmethod
    def fetch(self) -> List[NewsArticle]:
        """
        Fetch news articles from the source.
        
        Returns:
            List of NewsArticle objects
            
        Raises:
            Exception: If fetching fails
        """
        pass
    
    def validate_article(self, article: NewsArticle) -> bool:
        """
        Validate that an article has required fields.
        
        Args:
            article: NewsArticle to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not article.title or not article.url or not article.summary:
            logger.warning(f"Invalid article from {self.name}: missing required fields")
            return False
        return True
