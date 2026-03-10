"""Shared fixtures for AutoApply test suite."""

from __future__ import annotations

import pytest


@pytest.fixture
def mock_data_dir(tmp_path, monkeypatch):
    """Redirect get_data_dir() to a temporary directory for filesystem isolation."""
    monkeypatch.setattr("config.settings.get_data_dir", lambda: tmp_path)
    return tmp_path


@pytest.fixture
def valid_profile_data() -> dict:
    """Minimal valid UserProfile data."""
    return {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane@example.com",
        "phone_country_code": "+1",
        "phone": "555-0100",
        "city": "New York",
        "state": "NY",
        "bio": "Experienced software engineer.",
        "linkedin_url": "https://linkedin.com/in/janedoe",
    }


@pytest.fixture
def valid_search_criteria_data() -> dict:
    """Minimal valid SearchCriteria data."""
    return {
        "job_titles": ["Software Engineer"],
        "locations": ["Remote"],
    }


@pytest.fixture
def valid_app_config_data(valid_profile_data, valid_search_criteria_data) -> dict:
    """Full valid AppConfig data dictionary."""
    return {
        "profile": valid_profile_data,
        "search_criteria": valid_search_criteria_data,
        "bot": {},
    }
