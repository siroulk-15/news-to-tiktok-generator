"""Deterministic story scoring for the V0.2 pipeline."""

from datetime import datetime
from sqlalchemy.orm import Session

from app.database import StoryDB
from app.logger import setup_logger

logger = setup_logger(__name__)


class StoryScorer:
    """Calculate bounded, explainable scores without external services."""

    INSOLITE_KEYWORDS = {
        "bizarre", "strange", "unusual", "unexpected",
        "rare", "mystery", "mysterious", "insolite", "extraordinary",
    }

    def __init__(self, db: Session):
        self.db = db

    def score_stories(self, hours: int | None = None) -> dict:
        """Score stories, optionally limited to recently updated stories."""
        query = self.db.query(StoryDB)
        if hours is not None:
            cutoff = datetime.utcnow().timestamp() - (hours * 3600)
            query = query.filter(StoryDB.updated_at >= datetime.fromtimestamp(cutoff))

        stories = query.all()
        for story in stories:
            scores = self.calculate(story.title, story.summary, story.source_count)
            story.insolite_score = scores["insolite_score"]
            story.relevance_score = scores["relevance_score"]
            story.virality_score = scores["virality_score"]
            story.confidence_score = scores["confidence_score"]
            story.updated_at = datetime.utcnow()

        self.db.commit()
        logger.info("Scored %d stories", len(stories))
        return {"stories_scored": len(stories)}

    @classmethod
    def calculate(
        cls,
        title: str,
        summary: str,
        source_count: int = 1,
    ) -> dict[str, float]:
        """Return deterministic scores in the inclusive range [0, 1]."""
        text = f"{title} {summary}".lower()
        words = cls._words(text)
        unusual_hits = sum(keyword in text for keyword in cls.INSOLITE_KEYWORDS)
        unusual_score = min(1.0, 0.35 + (0.15 * unusual_hits))

        relevance_score = min(1.0, 0.35 + (0.03 * min(len(words), 20)))
        virality_score = min(
            1.0,
            0.25 + (0.25 * unusual_score) + (0.05 * min(len(title.split()), 8)),
        )
        confidence_score = min(1.0, 0.5 + (0.15 * max(source_count - 1, 0)))

        return {
            "insolite_score": cls._bounded(unusual_score),
            "relevance_score": cls._bounded(relevance_score),
            "virality_score": cls._bounded(virality_score),
            "confidence_score": cls._bounded(confidence_score),
        }

    @staticmethod
    def _words(text: str) -> list[str]:
        return [word for word in text.split() if word]

    @staticmethod
    def _bounded(value: float) -> float:
        return round(max(0.0, min(1.0, value)), 4)