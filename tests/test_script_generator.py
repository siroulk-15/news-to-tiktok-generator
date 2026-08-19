"""Tests for safe script draft generation."""

from datetime import datetime

from app.database import ScriptDraftDB, StoryDB
from app.services.script_generator import ScriptGenerator


def test_generate_uses_only_cleaned_story_content():
    draft = ScriptGenerator.generate(
        "  Strange   event  ",
        "A report\nwith limited details.",
    )

    assert draft["hook"] == "Strange event"
    assert draft["context"] == "A report with limited details."
    assert "Strange event" in draft["draft_text"]
    assert "A report with limited details." in draft["draft_text"]


def test_generate_for_selected_persists_and_is_idempotent(db_session):
    story = StoryDB(
        id="story-selected",
        title="Selected story",
        summary="Verified summary.",
        status="SELECTED",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(story)
    db_session.commit()

    generator = ScriptGenerator(db_session)
    assert generator.generate_for_selected() == {
        "stories_processed": 1,
        "drafts_created": 1,
        "drafts_updated": 0,
    }
    assert generator.generate_for_selected() == {
        "stories_processed": 1,
        "drafts_created": 0,
        "drafts_updated": 1,
    }

    draft = db_session.query(ScriptDraftDB).one()
    assert draft.status == "DRAFT"
    assert draft.story_id == story.id