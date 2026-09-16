from fastapi.testclient import TestClient

from src import app as app_module

client = TestClient(app_module.app)


def test_cannot_sign_up_twice_for_same_activity():
    activity_name = "Test Club"
    email = "student@example.edu"

    app_module.activities[activity_name] = {
        "description": "Temporary test activity",
        "schedule": "Mondays, 4:00 PM",
        "max_participants": 3,
        "participants": [],
    }

    first_response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert first_response.status_code == 200

    second_response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "Student already signed up"
