from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module

client = TestClient(app_module.app)


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(original_activities)


def add_test_activity(name="Test Club", participants=None, max_participants=3):
    app_module.activities[name] = {
        "description": "Temporary test activity",
        "schedule": "Mondays, 4:00 PM",
        "max_participants": max_participants,
        "participants": participants or [],
    }


def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data():
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json()["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_sign_up_adds_participant():
    activity_name = "Test Club"
    email = "student@example.edu"
    add_test_activity(activity_name)

    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert email in app_module.activities[activity_name]["participants"]


def test_sign_up_rejects_unknown_activity():
    response = client.post(
        "/activities/Missing%20Club/signup?email=student%40example.edu"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_cannot_sign_up_twice_for_same_activity():
    activity_name = "Test Club"
    email = "student@example.edu"
    add_test_activity(activity_name, participants=[email])

    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up"


def test_sign_up_rejects_full_activity():
    activity_name = "Full Club"
    add_test_activity(
        activity_name,
        participants=["first@example.edu"],
        max_participants=1,
    )

    response = client.post(
        f"/activities/{activity_name}/signup?email=second@example.edu"
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


def test_delete_removes_participant():
    activity_name = "Test Club"
    email = "student@example.edu"
    add_test_activity(activity_name, participants=[email])

    response = client.delete(
        f"/activities/{activity_name}/participants/{email}"
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Removed {email} from {activity_name}"
    }
    assert email not in app_module.activities[activity_name]["participants"]


def test_delete_rejects_unknown_activity():
    response = client.delete(
        "/activities/Missing%20Club/participants/student%40example.edu"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_delete_rejects_unknown_participant():
    activity_name = "Test Club"
    add_test_activity(activity_name)

    response = client.delete(
        f"/activities/{activity_name}/participants/missing@example.edu"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"
