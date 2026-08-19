"""Tests for the editorial review gate."""

from datetime import datetime

import pytest

from app.database import ScriptDraftDB, StoryDB
from app.services.workflow import EditorialWorkflow


def add_review_item(db_session):
    story = StoryDB(
        id="story-review",
        title="Review me",
        summary="Summary",
        status="SELECTED",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    draft = ScriptDraftDB(
        id="draft-review",
        story_id=story.id,
        hook="Review me",
        context="Summary",
        call_to_action="Follow updates.",
        draft_text="Review me\n\nSummary",
    )
    db_session.add_all([story, draft])
    db_session.commit()
    return story


def test_approve_transitions_story_and_draft(db_session):
    story = add_review_item(db_session)

    EditorialWorkflow(db_session).approve(story.id)

    assert db_session.get(StoryDB, story.id).status == "APPROVED"
    assert db_session.get(ScriptDraftDB, "draft-review").status == "APPROVED"


def test_reject_requires_selected_status(db_session):
    story = add_review_item(db_session)
    workflow = EditorialWorkflow(db_session)
    workflow.reject(story.id)

    with pytest.raises(ValueError, match="cannot transition"):
        workflow.approve(story.id)


def test_review_queue_only_returns_selected_stories(db_session):
    add_review_item(db_session)
    db_session.add(StoryDB(
        id="story-approved",
        title="Already approved",
        summary="Summary",
        status="APPROVED",
    ))
    db_session.commit()

    queue = EditorialWorkflow(db_session).review_queue()

    assert [story.id for story in queue] == ["story-review"]