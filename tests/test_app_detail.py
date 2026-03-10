"""Unit tests for Application Detail View feature.

Requirement traceability:
    FR-065 — Application detail endpoint (GET /api/applications/:id)
    FR-066 — Application events endpoint (GET /api/applications/:id/events)
    FR-067 — PATCH applications with partial updates (notes-only)
"""

from __future__ import annotations

import json

import pytest

from db.database import Database


def insert_app(db: Database, **kwargs) -> int:
    """Insert a test application with sensible defaults."""
    defaults = dict(
        external_id="job1",
        platform="linkedin",
        job_title="Engineer",
        company="Acme",
        location="NYC",
        salary="100k",
        apply_url="https://example.com",
        match_score=85,
        resume_path=None,
        cover_letter_path=None,
        cover_letter_text="Dear Hiring Manager...",
        status="applied",
        error_message=None,
    )
    defaults.update(kwargs)
    return db.save_application(**defaults)


@pytest.fixture
def app_client(tmp_path, monkeypatch):
    """Yield (test_client, db, tmp_path) with all paths redirected to tmp_path."""
    monkeypatch.setattr("config.settings.get_data_dir", lambda: tmp_path)
    monkeypatch.setattr("app.get_data_dir", lambda: tmp_path)

    (tmp_path / "profile" / "experiences").mkdir(parents=True)

    minimal_config = {
        "profile": {
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "phone": "555-0100",
            "city": "Remote",
            "state": "",
            "bio": "Test bio",
        },
        "search_criteria": {
            "job_titles": ["Software Engineer"],
            "locations": ["Remote"],
        },
        "bot": {"enabled_platforms": ["linkedin"]},
    }
    (tmp_path / "config.json").write_text(json.dumps(minimal_config), encoding="utf-8")

    test_db = Database(tmp_path / "test.db")
    monkeypatch.setattr("app.db", test_db)

    from app import app

    app.config["TESTING"] = True
    return app.test_client(), test_db, tmp_path


# ===================================================================
# FR-065 — GET /api/applications/:id
# ===================================================================


class TestGetApplicationDetail:
    """FR-065: Single application detail endpoint."""

    def test_get_existing_application(self, app_client):
        """FR-065: Returns full application data for valid ID."""
        client, db, _ = app_client
        app_id = insert_app(db, job_title="Senior Dev", company="BigCorp", salary="150k")

        res = client.get(f"/api/applications/{app_id}")
        assert res.status_code == 200
        data = res.get_json()
        assert data["id"] == app_id
        assert data["job_title"] == "Senior Dev"
        assert data["company"] == "BigCorp"
        assert data["salary"] == "150k"
        assert data["platform"] == "linkedin"
        assert data["match_score"] == 85
        assert data["status"] == "applied"
        assert "applied_at" in data
        assert "updated_at" in data

    def test_get_nonexistent_application(self, app_client):
        """FR-065: Returns 404 for non-existent ID."""
        client, _, _ = app_client
        res = client.get("/api/applications/9999")
        assert res.status_code == 404
        assert "not found" in res.get_json()["error"].lower()

    def test_get_application_includes_all_fields(self, app_client):
        """FR-065: Response includes all 17 Application model fields."""
        client, db, _ = app_client
        app_id = insert_app(
            db,
            job_title="ML Engineer",
            error_message="Form timeout",
            cover_letter_text="Hello...",
            status="error",
        )

        res = client.get(f"/api/applications/{app_id}")
        data = res.get_json()
        expected_fields = [
            "id", "external_id", "platform", "job_title", "company",
            "location", "salary", "apply_url", "match_score", "resume_path",
            "cover_letter_path", "cover_letter_text", "status",
            "error_message", "applied_at", "updated_at", "notes",
        ]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        assert data["error_message"] == "Form timeout"


# ===================================================================
# FR-066 — GET /api/applications/:id/events
# ===================================================================


class TestGetApplicationEvents:
    """FR-066: Application-specific feed events."""

    def test_events_for_application(self, app_client):
        """FR-066: Returns feed events matching the application's job_title and company."""
        client, db, _ = app_client
        app_id = insert_app(db, job_title="Backend Dev", company="TechCo")

        # Insert matching feed events
        db.save_feed_event("FOUND", job_title="Backend Dev", company="TechCo", message="Found job")
        db.save_feed_event("APPLIED", job_title="Backend Dev", company="TechCo", message="Applied")
        # Insert non-matching event
        db.save_feed_event("FOUND", job_title="Frontend Dev", company="OtherCo", message="Different job")

        res = client.get(f"/api/applications/{app_id}/events")
        assert res.status_code == 200
        events = res.get_json()
        assert len(events) == 2
        assert all(e["company"] == "TechCo" for e in events)

    def test_events_for_nonexistent_application(self, app_client):
        """FR-066: Returns 404 for non-existent application."""
        client, _, _ = app_client
        res = client.get("/api/applications/9999/events")
        assert res.status_code == 404

    def test_events_empty_when_no_matching(self, app_client):
        """FR-066: Returns empty list when no events match."""
        client, db, _ = app_client
        app_id = insert_app(db, job_title="Unique Role", company="UniqueCo")

        res = client.get(f"/api/applications/{app_id}/events")
        assert res.status_code == 200
        assert res.get_json() == []


# ===================================================================
# FR-067 — PATCH with partial updates
# ===================================================================


class TestPatchApplication:
    """FR-067: Partial update support for applications."""

    def test_update_status_only(self, app_client):
        """FR-067: PATCH with status only updates status, preserves notes."""
        client, db, _ = app_client
        app_id = insert_app(db)
        db.update_status(app_id, "applied", "Initial note")

        res = client.patch(
            f"/api/applications/{app_id}",
            json={"status": "interview"},
        )
        assert res.status_code == 200

        updated = db.get_application(app_id)
        assert updated.status == "interview"
        assert updated.notes == "Initial note"

    def test_update_notes_only(self, app_client):
        """FR-067: PATCH with notes only updates notes, preserves status."""
        client, db, _ = app_client
        app_id = insert_app(db, status="applied")

        res = client.patch(
            f"/api/applications/{app_id}",
            json={"notes": "Follow up next week"},
        )
        assert res.status_code == 200

        updated = db.get_application(app_id)
        assert updated.status == "applied"
        assert updated.notes == "Follow up next week"

    def test_update_both_status_and_notes(self, app_client):
        """FR-067: PATCH with both fields updates both."""
        client, db, _ = app_client
        app_id = insert_app(db)

        res = client.patch(
            f"/api/applications/{app_id}",
            json={"status": "offer", "notes": "Great news!"},
        )
        assert res.status_code == 200

        updated = db.get_application(app_id)
        assert updated.status == "offer"
        assert updated.notes == "Great news!"

    def test_patch_nonexistent_returns_404(self, app_client):
        """FR-067: PATCH on non-existent application returns 404."""
        client, _, _ = app_client
        res = client.patch(
            "/api/applications/9999",
            json={"status": "interview"},
        )
        assert res.status_code == 404

    def test_patch_empty_body_returns_400(self, app_client):
        """FR-067: PATCH with empty body returns 400."""
        client, db, _ = app_client
        insert_app(db)
        res = client.patch(
            "/api/applications/1",
            data="",
            content_type="application/json",
        )
        assert res.status_code == 400


# ===================================================================
# Database — get_feed_events_for_job
# ===================================================================


class TestGetFeedEventsForJob:
    """Database method for job-specific feed events."""

    def test_returns_matching_events(self, tmp_path):
        """Returns events matching both job_title and company."""
        db = Database(tmp_path / "test.db")
        db.save_feed_event("FOUND", job_title="Dev", company="Acme", message="Found")
        db.save_feed_event("APPLIED", job_title="Dev", company="Acme", message="Applied")
        db.save_feed_event("FOUND", job_title="Dev", company="Other", message="Wrong co")

        events = db.get_feed_events_for_job("Dev", "Acme")
        assert len(events) == 2
        assert all(e.company == "Acme" for e in events)

    def test_returns_empty_for_no_match(self, tmp_path):
        """Returns empty list when no events match."""
        db = Database(tmp_path / "test.db")
        db.save_feed_event("FOUND", job_title="Dev", company="Acme")

        events = db.get_feed_events_for_job("Manager", "OtherCo")
        assert events == []

    def test_respects_limit(self, tmp_path):
        """Respects the limit parameter."""
        db = Database(tmp_path / "test.db")
        for i in range(10):
            db.save_feed_event("FOUND", job_title="Dev", company="Acme", message=f"Event {i}")

        events = db.get_feed_events_for_job("Dev", "Acme", limit=3)
        assert len(events) == 3

    def test_ordered_by_created_at_desc(self, tmp_path):
        """Events are returned newest first (by id as tiebreaker)."""
        db = Database(tmp_path / "test.db")
        db.save_feed_event("FOUND", job_title="Dev", company="Acme", message="First")
        db.save_feed_event("APPLIED", job_title="Dev", company="Acme", message="Second")

        events = db.get_feed_events_for_job("Dev", "Acme")
        # Both events returned; newest (higher ID) first when timestamps match
        assert len(events) == 2
        assert events[0].id > events[1].id
