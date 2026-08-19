"""Tests for safe script draft generation."""

from datetime import datetime

from app.database import ScriptDraftDB, StoryDB
from app.services.script_generator import ScriptGenerator


def test_generate_uses_only_cleaned_story_content():
    draft = ScriptGenerator.generate(
        "  Strange   event  ",
        "A report\nwith limited details.",
    )

    assert draft["hook"] == "Here is what matters: Strange event"
    assert draft["context"] == "A report with limited details."
    assert draft["language"] == "en"
    assert "Here is what matters" in draft["draft_text"]
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


def test_generate_keeps_french_content_in_french():
    draft = ScriptGenerator.generate(
        "Une nouvelle importante",
        "Le gouvernement annonce cette mesure après une réunion.",
    )

    assert draft["language"] == "fr"
    assert draft["hook"].startswith("Voici ce qu'il faut retenir")
    assert "Nous suivrons" in draft["call_to_action"]