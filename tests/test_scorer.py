"""Tests for deterministic story scoring."""

from datetime import datetime

from app.database import StoryDB
from app.services.scorer import StoryScorer


def test_calculate_returns_bounded_scores():
    scores = StoryScorer.calculate(
        "Strange discovery shocks scientists",
        "An unusual event was reported by three sources.",
        source_count=3,
    )

    assert set(scores) == {
        "insolite_score",
        "relevance_score",
        "virality_score",
        "confidence_score",
    }
    assert all(0.0 <= value <= 1.0 for value in scores.values())
    assert scores["confidence_score"] == 0.8
    assert scores["insolite_score"] > 0.35


def test_calculate_is_deterministic():
    inputs = ("Routine update", "A standard report was published.", 1)
    assert StoryScorer.calculate(*inputs) == StoryScorer.calculate(*inputs)


def test_score_stories_persists_scores(db_session):
    story = StoryDB(
        id="story-1",
        title="Unusual event reported",
        summary="A strange event happened today.",
        source_count=2,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(story)
    db_session.commit()

    stats = StoryScorer(db_session).score_stories()

    assert stats == {"stories_scored": 1}
    db_session.refresh(story)
    assert story.insolite_score is not None
    assert story.relevance_score is not None
    assert story.virality_score is not None
    assert story.confidence_score == 0.65