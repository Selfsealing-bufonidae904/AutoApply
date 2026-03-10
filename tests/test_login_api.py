"""Unit tests for login browser API endpoints.

Requirement traceability:
    FR-068  Platform login browser endpoints
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from db.database import Database


@pytest.fixture
def app_client(tmp_path, monkeypatch):
    """Yield (test_client, tmp_path) with paths redirected to tmp_path."""
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
        "search_criteria": {"job_titles": ["Engineer"], "locations": ["Remote"]},
        "bot": {"enabled_platforms": ["linkedin"]},
    }
    (tmp_path / "config.json").write_text(json.dumps(minimal_config), encoding="utf-8")

    test_db = Database(tmp_path / "test.db")
    monkeypatch.setattr("app.db", test_db)

    import app as app_module

    # Reset login state between tests
    monkeypatch.setattr(app_module, "_login_proc", None)

    app_module.app.config["TESTING"] = True
    return app_module.app.test_client(), tmp_path


class TestLoginOpen:
    """POST /api/login/open — opens system Chrome for platform login."""

    def test_missing_url_returns_400(self, app_client):
        client, _ = app_client
        rv = client.post("/api/login/open", json={})
        assert rv.status_code == 400
        assert "url" in rv.get_json()["error"]

    def test_no_body_returns_400(self, app_client):
        client, _ = app_client
        rv = client.post(
            "/api/login/open",
            data="",
            content_type="application/json",
        )
        assert rv.status_code == 400

    def test_disallowed_domain_returns_400(self, app_client):
        client, _ = app_client
        rv = client.post("/api/login/open", json={"url": "https://evil.com/login"})
        assert rv.status_code == 400
        assert "Only LinkedIn and Indeed" in rv.get_json()["error"]

    @patch("app._find_system_chrome", return_value=None)
    def test_no_chrome_returns_500(self, _mock, app_client):
        client, _ = app_client
        rv = client.post(
            "/api/login/open",
            json={"url": "https://www.linkedin.com/login"},
        )
        assert rv.status_code == 500
        assert "Chrome not found" in rv.get_json()["error"]

    @patch("app.subprocess.Popen")
    @patch("app._find_system_chrome", return_value="C:/chrome.exe")
    def test_valid_linkedin_url_returns_opening(self, _chrome, mock_popen, app_client):
        client, _ = app_client
        mock_popen.return_value = MagicMock(pid=1234)
        rv = client.post(
            "/api/login/open",
            json={"url": "https://www.linkedin.com/login"},
        )
        assert rv.status_code == 200
        assert rv.get_json()["status"] == "opening"
        mock_popen.assert_called_once()

    @patch("app.subprocess.Popen")
    @patch("app._find_system_chrome", return_value="C:/chrome.exe")
    def test_valid_indeed_url_returns_opening(self, _chrome, mock_popen, app_client):
        client, _ = app_client
        mock_popen.return_value = MagicMock(pid=1234)
        rv = client.post(
            "/api/login/open",
            json={"url": "https://secure.indeed.com/auth"},
        )
        assert rv.status_code == 200
        assert rv.get_json()["status"] == "opening"

    @patch("app.subprocess.Popen")
    @patch("app._find_system_chrome", return_value="C:/chrome.exe")
    def test_already_open_terminates_old(self, _chrome, mock_popen, app_client, monkeypatch):
        """If a browser is already open, it terminates the old process."""
        client, _ = app_client
        import app as app_module

        fake_proc = MagicMock()
        monkeypatch.setattr(app_module, "_login_proc", fake_proc)

        mock_popen.return_value = MagicMock(pid=5678)
        rv = client.post(
            "/api/login/open",
            json={"url": "https://www.linkedin.com/login"},
        )
        assert rv.status_code == 200
        fake_proc.terminate.assert_called_once()


class TestLoginClose:
    """POST /api/login/close — closes the login browser."""

    def test_close_when_not_open_returns_already_closed(self, app_client):
        client, _ = app_client
        rv = client.post("/api/login/close")
        assert rv.status_code == 200
        assert rv.get_json()["status"] == "already_closed"

    def test_close_when_open_terminates_process(self, app_client, monkeypatch):
        client, _ = app_client
        import app as app_module

        fake_proc = MagicMock()
        monkeypatch.setattr(app_module, "_login_proc", fake_proc)
        rv = client.post("/api/login/close")
        assert rv.status_code == 200
        assert rv.get_json()["status"] == "closed"
        fake_proc.terminate.assert_called_once()
        assert app_module._login_proc is None


class TestLoginStatus:
    """GET /api/login/status — reports whether a login browser is open."""

    def test_status_when_closed(self, app_client):
        client, _ = app_client
        rv = client.get("/api/login/status")
        assert rv.status_code == 200
        assert rv.get_json()["open"] is False

    def test_status_when_running(self, app_client, monkeypatch):
        client, _ = app_client
        import app as app_module

        fake_proc = MagicMock()
        fake_proc.poll.return_value = None  # still running
        monkeypatch.setattr(app_module, "_login_proc", fake_proc)
        rv = client.get("/api/login/status")
        assert rv.status_code == 200
        assert rv.get_json()["open"] is True

    def test_status_exited_process_auto_cleans(self, app_client, monkeypatch):
        """If Chrome process exited, status returns false and cleans up."""
        client, _ = app_client
        import app as app_module

        fake_proc = MagicMock()
        fake_proc.poll.return_value = 0  # process exited
        monkeypatch.setattr(app_module, "_login_proc", fake_proc)
        rv = client.get("/api/login/status")
        assert rv.status_code == 200
        assert rv.get_json()["open"] is False
        assert app_module._login_proc is None
