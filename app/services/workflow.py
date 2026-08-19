"""Editorial review workflow for story and script draft approval."""

from sqlalchemy.orm import Session

from app.database import ScriptDraftDB, StoryDB
from app.logger import setup_logger

logger = setup_logger(__name__)


class EditorialWorkflow:
    """Enforce an explicit review gate before downstream automation."""

    def __init__(self, db: Session):
        self.db = db

    def review_queue(self, limit: int | None = None) -> list[StoryDB]:
        """Return selected stories that are ready for editorial review."""
        query = self.db.query(StoryDB).filter(StoryDB.status == "SELECTED")
        query = query.order_by(StoryDB.updated_at.desc())
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    def approve(self, story_id: str) -> StoryDB:
        """Approve one selected story and its draft."""
        return self._transition(story_id, "APPROVED")

    def reject(self, story_id: str) -> StoryDB:
        """Reject one selected story and its draft."""
        return self._transition(story_id, "REJECTED")

    def _transition(self, story_id: str, status: str) -> StoryDB:
        story = self.db.query(StoryDB).filter(StoryDB.id == story_id).first()
        if story is None:
            raise ValueError(f"Story not found: {story_id}")
        if story.status != "SELECTED":
            raise ValueError(
                f"Story {story_id} cannot transition from status {story.status}"
            )

        story.status = status
        draft = self.db.query(ScriptDraftDB).filter(
            ScriptDraftDB.story_id == story_id
        ).first()
        if draft is not None:
            draft.status = status

        self.db.commit()
        logger.info("Story %s transitioned to %s", story_id, status)
        return story