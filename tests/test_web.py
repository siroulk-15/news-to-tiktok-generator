"""Tests for the local editorial web interface."""

from datetime import datetime

import pytest

from app import web
from app.database import ScriptDraftDB, StoryDB


def add_review_item(db_session, status="SELECTED"):
    story = StoryDB(
        id="story-web",
        title="Web review story",
        summary="A concise story summary.",
        status=status,
        source_count=2,
        insolite_score=0.7,
        confidence_score=0.8,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    draft = ScriptDraftDB(
        id="draft-web",
        story_id=story.id,
        hook="Web review story",
        context="A concise story summary.",
        call_to_action="Follow updates.",
        draft_text="Web review story\n\nA concise story summary.",
    )
    db_session.add_all([story, draft])
    db_session.commit()
    return story


def patch_web_database(monkeypatch, db_session):
    monkeypatch.setattr(web, "init_db", lambda: None)
    monkeypatch.setattr(web, "get_db", lambda: db_session)
    monkeypatch.setattr(web, "close_db", lambda db: None)


def test_home_contains_review_interface():
    response = web.home()

    assert "Revue" in response
    assert "/api/review" in response
    assert "Approuver" in response


def test_review_api_includes_draft_content(db_session, monkeypatch):
    add_review_item(db_session)
    patch_web_database(monkeypatch, db_session)

    items = web.review_queue()

    assert items == [{
        "id": "story-web",
        "title": "Web review story",
        "summary": "A concise story summary.",
        "status": "SELECTED",
        "source_count": 2,
        "insolite_score": 0.7,
        "confidence_score": 0.8,
        "draft_text": "Web review story\n\nA concise story summary.",
    }]


def test_approve_endpoint_returns_transition(db_session, monkeypatch):
    story = add_review_item(db_session)
    patch_web_database(monkeypatch, db_session)

    response = web.approve(story.id)

    assert response == {"id": story.id, "status": "APPROVED"}


def test_reject_endpoint_returns_conflict_for_non_selected(db_session, monkeypatch):
    story = add_review_item(db_session, status="APPROVED")
    patch_web_database(monkeypatch, db_session)

    with pytest.raises(web.HTTPException) as error:
        web.reject(story.id)

    assert error.value.status_code == 409