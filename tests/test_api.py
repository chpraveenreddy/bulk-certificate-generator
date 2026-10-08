from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_home():
    response = client.get("/")
    assert response.status_code == 200


def test_create_job():
    response = client.post(
        "/jobs",
        json={
            "event_name": "Test Event",
            "recipients": [
                {
                    "name": "Test User",
                    "email": "test@example.com",
                    "achievement": "Participation"
                }
            ]
        }
    )

    assert response.status_code == 202

    data = response.json()

    assert data["event_name"] == "Test Event"
    assert data["total"] == 1