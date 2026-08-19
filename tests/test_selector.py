"""Tests for score-based story selection."""

from datetime import datetime

import pytest

from app.database import StoryDB
from app.services.selector import StorySelector


def make_story(story_id, insolite, confidence, status="NEW"):
    return StoryDB(
        id=story_id,
        title=story_id,
        summary="Summary",
        status=status,
        insolite_score=insolite,
        relevance_score=0.8,
        virality_score=0.7,
        confidence_score=confidence,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


def test_select_updates_status_and_ranks_stories(db_session):
    db_session.add_all([
        make_story("low", 0.6, 0.9),
        make_story("high", 0.9, 0.9),
        make_story("reviewed", 0.1, 0.1, status="VERIFIED"),
    ])
    db_session.commit()

    stats = StorySelector(db_session).select(0.65, 0.8)

    assert stats["stories_reviewed"] == 2
    assert stats["stories_selected"] == 1
    assert stats["stories_filtered"] == 1
    assert [story.id for story in stats["selected_stories"]] == ["high"]
    assert db_session.get(StoryDB, "low").status == "FILTERED"
    assert db_session.get(StoryDB, "reviewed").status == "VERIFIED"


@pytest.mark.parametrize("value", [-0.1, 1.1])
def test_select_rejects_invalid_thresholds(db_session, value):
    with pytest.raises(ValueError):
        StorySelector(db_session).select(value, 0.8)