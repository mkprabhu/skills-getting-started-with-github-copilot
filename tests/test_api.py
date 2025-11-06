import copy
import os
import sys
from pathlib import Path

# Ensure src is importable
ROOT = Path(__file__).resolve().parent.parent
SRC = str(ROOT / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

import app as app_module
from fastapi.testclient import TestClient
import pytest

client = TestClient(app_module.app)

@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the in-memory activities dict before/after each test to avoid cross-test pollution."""
    original = copy.deepcopy(app_module.activities)
    try:
        yield
    finally:
        app_module.activities.clear()
        app_module.activities.update(original)


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # Basic sanity checks for a few known activities
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_success():
    activity = "Chess Club"
    email = "pytest-user@example.com"
    # Ensure email not already present
    assert email not in app_module.activities[activity]["participants"]

    resp = client.post(f"/activities/{activity}/signup?email={email}")
    assert resp.status_code == 200
    payload = resp.json()
    assert "Signed up" in payload.get("message", "")
    # Now check server state changed
    assert email in app_module.activities[activity]["participants"]


def test_signup_already_registered():
    activity = "Chess Club"
    existing = app_module.activities[activity]["participants"][0]
    resp = client.post(f"/activities/{activity}/signup?email={existing}")
    assert resp.status_code == 400
    assert resp.json().get("detail") == "Student is already signed up"


def test_signup_activity_not_found():
    resp = client.post("/activities/NoSuchActivity/signup?email=doesnotmatter@example.com")
    assert resp.status_code == 404
