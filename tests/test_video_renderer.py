"""Tests for local approved video rendering."""

from datetime import datetime

from app.database import ScriptDraftDB, StoryDB
from app.services.video_renderer import VideoRenderer


def test_render_approved_ignores_unapproved_content(db_session, tmp_path):
    story = StoryDB(
        id="story-video",
        title="Video story",
        summary="Summary",
        status="SELECTED",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    draft = ScriptDraftDB(
        id="draft-video",
        story_id=story.id,
        hook="Hook",
        context="Context",
        call_to_action="CTA",
        draft_text="Hook\nContext\nCTA",
        status="DRAFT",
    )
    db_session.add_all([story, draft])
    db_session.commit()

    stats = VideoRenderer(db_session).render_approved(tmp_path)

    assert stats["videos_rendered"] == 0
    assert not list(tmp_path.glob("*.mp4"))


def test_render_draft_creates_mp4(db_session, tmp_path):
    draft = ScriptDraftDB(
        id="draft-render",
        story_id="story-render",
        hook="Hook",
        context="Context",
        call_to_action="CTA",
        draft_text="Hook\nContext\nCTA",
        status="APPROVED",
    )

    output = tmp_path / "test.mp4"
    VideoRenderer(db_session).render_draft(
        draft, output, width=160, height=288, fps=5, slide_seconds=1
    )

    assert output.exists()
    assert output.stat().st_size > 1000