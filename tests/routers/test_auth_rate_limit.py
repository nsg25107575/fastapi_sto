from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_sign_in_rate_limit():
    """The sixth sign-in request from the same IP is rejected."""
    for _ in range(5):
        response = client.post(
            "/auth/sign-in",
            json={
                "email": "unknown@example.com",
                "password": "StrongPassword123!",
            },
        )
        assert response.status_code == 401

    response = client.post(
        "/auth/sign-in",
        json={
            "email": "unknown@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 429
    assert response.json() == {
        "success": False,
        "message": "Too many requests",
        "data": None,
    }


def test_sign_up_rate_limit():
    """The sixth sign-up request from the same IP is rejected."""
    for i in range(5):
        response = client.post(
            "/auth/sign-up",
            json={
                "email": f"user{i}@example.com",
                "password": "StrongPassword123!",
                "first_name": "John",
                "last_name": "Doe",
                "second_name": "Smith",
            },
        )
        assert response.status_code == 201

    response = client.post(
        "/auth/sign-up",
        json={
            "email": "user5@example.com",
            "password": "StrongPassword123!",
            "first_name": "John",
            "last_name": "Doe",
            "second_name": "Smith",
        },
    )

    assert response.status_code == 429
    assert response.json() == {
        "success": False,
        "message": "Too many requests",
        "data": None,
    }
