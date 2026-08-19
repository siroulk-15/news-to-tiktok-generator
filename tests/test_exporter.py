"""Tests for approved content export."""

import json
from datetime import datetime

from app.database import ScriptDraftDB, StoryDB
from app.services.exporter import ApprovedContentExporter


def test_export_only_writes_approved_story_and_draft(db_session, tmp_path):
    approved = StoryDB(
        id="story-approved",
        title="Approved story",
        summary="Approved summary",
        status="APPROVED",
        source_count=2,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    draft = ScriptDraftDB(
        id="draft-approved",
        story_id=approved.id,
        hook="Approved story",
        context="Approved summary",
        call_to_action="Follow updates.",
        draft_text="Approved story\n\nApproved summary",
        status="APPROVED",
    )
    pending = StoryDB(
        id="story-pending",
        title="Pending story",
        summary="Pending summary",
        status="SELECTED",
    )
    db_session.add_all([approved, draft, pending])
    db_session.commit()

    stats = ApprovedContentExporter(db_session).export(tmp_path)

    assert stats["stories_exported"] == 1
    assert (tmp_path / "story-approved.txt").read_text() == draft.draft_text
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["count"] == 1
    assert manifest["items"][0]["story_id"] == approved.id
    assert not (tmp_path / "story-pending.txt").exists()