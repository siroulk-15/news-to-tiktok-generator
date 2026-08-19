"""Export approved stories for manual video production."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.database import ScriptDraftDB, StoryDB
from app.logger import setup_logger

logger = setup_logger(__name__)


class ApprovedContentExporter:
    """Export only approved stories and approved script drafts."""

    def __init__(self, db: Session):
        self.db = db

    def export(self, output_dir: str | Path) -> dict:
        """Write approved content to a timestamped, reproducible package."""
        destination = Path(output_dir)
        destination.mkdir(parents=True, exist_ok=True)
        stories = self.db.query(StoryDB).filter(StoryDB.status == "APPROVED").all()
        exported = []

        for story in stories:
            draft = self.db.query(ScriptDraftDB).filter(
                ScriptDraftDB.story_id == story.id,
                ScriptDraftDB.status == "APPROVED",
            ).first()
            if draft is None:
                continue

            safe_id = re.sub(r"[^a-zA-Z0-9._-]+", "-", story.id).strip("-")
            script_path = destination / f"{safe_id}.txt"
            script_path.write_text(draft.draft_text, encoding="utf-8")
            exported.append({
                "story_id": story.id,
                "title": story.title,
                "summary": story.summary,
                "script_file": script_path.name,
                "source_count": story.source_count,
            })

        manifest = {
            "format": "ntg-approved-content-v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "count": len(exported),
            "items": exported,
        }
        (destination / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info("Exported %d approved story package(s) to %s", len(exported), destination)
        return {"stories_exported": len(exported), "output_dir": str(destination)}