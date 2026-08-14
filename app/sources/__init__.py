"""News sources module."""

from app.sources.base import BaseNewsSource
from app.sources.rss import RSSNewsSource

__all__ = ["BaseNewsSource", "RSSNewsSource"]
