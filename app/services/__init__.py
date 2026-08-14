"""Services module."""

from app.services.news_collector import NewsCollector
from app.services.deduplicator import Deduplicator

__all__ = ["NewsCollector", "Deduplicator"]
