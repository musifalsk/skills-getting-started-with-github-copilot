from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture(autouse=True)
def reset_activities_state():
    original_activities = deepcopy(app_module.activities)
    yield
    app_module.activities = deepcopy(original_activities)


@pytest.fixture
def client():
    return TestClient(app_module.app)


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client):
    response = client.get("/activities")

    assert response.status_code == 200
    body = response.json()
    assert "Chess Club" in body
    assert body["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_adds_student_to_activity(client):
    email = "newstudent@mergington.edu"

    response = client.post(f"/activities/Chess Club/signup?email={email}")

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert email in app_module.activities["Chess Club"]["participants"]


def test_signup_rejects_duplicate_student(client):
    response = client.post("/activities/Chess Club/signup?email=michael@mergington.edu")

    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}


def test_signup_returns_not_found_for_unknown_activity(client):
    response = client.post("/activities/Unknown Club/signup?email=student@mergington.edu")

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_removes_student_from_activity(client):
    email = "michael@mergington.edu"

    response = client.delete(f"/activities/Chess Club/participants/{email}")

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Chess Club"}
    assert email not in app_module.activities["Chess Club"]["participants"]


def test_unregister_returns_not_found_for_unknown_activity(client):
    response = client.delete("/activities/Unknown Club/participants/student@mergington.edu")

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_returns_not_found_for_missing_participant(client):
    response = client.delete("/activities/Chess Club/participants/not-enrolled@mergington.edu")

    assert response.status_code == 404
    assert response.json() == {"detail": "Participant not found in this activity"}