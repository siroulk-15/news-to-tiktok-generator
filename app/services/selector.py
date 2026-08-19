"""Select scored stories for downstream processing."""

from sqlalchemy.orm import Session

from app.database import StoryDB
from app.logger import setup_logger

logger = setup_logger(__name__)


class StorySelector:
    """Apply configurable thresholds and rank eligible stories."""

    WORKFLOW_STATUSES = ("NEW", "SELECTED", "FILTERED")

    def __init__(self, db: Session):
        self.db = db

    def select(self, min_insolite_score: float, min_confidence: float) -> dict:
        """Update workflow status and return selected stories by rank."""
        self._validate_threshold(min_insolite_score, "min_insolite_score")
        self._validate_threshold(min_confidence, "min_confidence")

        stories = self.db.query(StoryDB).filter(
            StoryDB.status.in_(self.WORKFLOW_STATUSES)
        ).all()
        selected = []

        for story in stories:
            is_selected = (
                story.insolite_score is not None
                and story.confidence_score is not None
                and story.insolite_score >= min_insolite_score
                and story.confidence_score >= min_confidence
            )
            story.status = "SELECTED" if is_selected else "FILTERED"
            if is_selected:
                selected.append(story)

        self.db.commit()
        selected.sort(key=self._ranking_score, reverse=True)
        logger.info("Selected %d of %d stories", len(selected), len(stories))
        return {
            "stories_reviewed": len(stories),
            "stories_selected": len(selected),
            "stories_filtered": len(stories) - len(selected),
            "selected_stories": selected,
        }

    @staticmethod
    def _ranking_score(story: StoryDB) -> float:
        return (
            (0.5 * (story.insolite_score or 0.0))
            + (0.3 * (story.relevance_score or 0.0))
            + (0.2 * (story.virality_score or 0.0))
        )

    @staticmethod
    def _validate_threshold(value: float, name: str) -> None:
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must be between 0 and 1")