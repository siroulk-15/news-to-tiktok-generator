"""Generate safe, extractive script drafts from selected stories."""

import hashlib
import re
from datetime import datetime

from sqlalchemy.orm import Session

from app.database import ScriptDraftDB, StoryDB
from app.logger import setup_logger

logger = setup_logger(__name__)


class ScriptGenerator:
    """Create draft scripts without adding facts beyond the source story."""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def generate(title: str, summary: str) -> dict[str, str]:
        """Build a short draft using only the provided title and summary."""
        clean_title = ScriptGenerator._clean(title, 180)
        clean_summary = ScriptGenerator._clean(summary, 500)
        hook = clean_title
        context = clean_summary or "Les informations disponibles sont encore limitées."
        call_to_action = "Nous suivrons cette affaire au fil des prochaines informations."

        return {
            "hook": hook,
            "context": context,
            "call_to_action": call_to_action,
            "draft_text": f"{hook}\n\n{context}\n\n{call_to_action}",
        }

    def generate_for_selected(self, limit: int | None = None) -> dict:
        """Persist drafts for selected stories, updating existing drafts safely."""
        query = self.db.query(StoryDB).filter(StoryDB.status == "SELECTED")
        if limit is not None:
            query = query.limit(limit)

        stories = query.all()
        created = 0
        updated = 0

        for story in stories:
            content = self.generate(story.title, story.summary)
            draft_id = f"draft-{hashlib.sha256(story.id.encode()).hexdigest()[:16]}"
            draft = self.db.query(ScriptDraftDB).filter(
                ScriptDraftDB.story_id == story.id
            ).first()

            if draft is None:
                draft = ScriptDraftDB(id=draft_id, story_id=story.id, **content)
                self.db.add(draft)
                created += 1
            else:
                for field, value in content.items():
                    setattr(draft, field, value)
                draft.updated_at = datetime.utcnow()
                draft.status = "DRAFT"
                updated += 1

        self.db.commit()
        logger.info("Generated %d new and updated %d script drafts", created, updated)
        return {
            "stories_processed": len(stories),
            "drafts_created": created,
            "drafts_updated": updated,
        }

    @staticmethod
    def _clean(value: str, max_length: int) -> str:
        normalized = re.sub(r"\s+", " ", value or "").strip()
        return normalized[:max_length]