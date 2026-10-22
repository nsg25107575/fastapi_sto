import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_sign_up_success():
    """Successful registration returns a consistent response envelope."""
    response = client.post(
        "/auth/sign-up",
        json={
            "email": "new_user@example.com",
            "password": "StrongPassword123!",
            "first_name": "John",
            "last_name": "Doe",
            "second_name": "Smith",
        },
    )

    assert response.status_code == 201

    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Registration successful"
    assert body["data"]["id"] is not None
    assert body["data"]["redirect_to"] == "/dashboard"

    # The token is stored in an HttpOnly cookie, not returned in JSON.
    assert "station" in response.cookies
    assert "token" not in body
    assert "access_token" not in body


def test_sign_up_duplicate_email():
    """Registering with an existing email returns an error response."""
    email = "duplicate_user@example.com"
    payload = {
        "email": email,
        "password": "StrongPassword123!",
        "first_name": "John",
        "last_name": "Doe",
        "second_name": "Smith",
    }

    first_response = client.post("/auth/sign-up", json=payload)
    assert first_response.status_code == 201

    response = client.post("/auth/sign-up", json=payload)

    assert response.status_code == 409
    body = response.json()
    assert body["success"] is False
    assert isinstance(body["message"], str)
    assert body["data"] is None


def test_sign_up_weak_password():
    """Weak passwords are rejected with the standardized validation envelope."""
    response = client.post(
        "/auth/sign-up",
        json={
            "email": "weak_password@example.com",
            "password": "weak",
            "first_name": "John",
            "last_name": "Doe",
            "second_name": "Smith",
        },
    )

    assert response.status_code == 422

    body = response.json()
    assert body["success"] is False
    assert body["message"] == "Validation error"
    assert isinstance(body["data"], list)
    assert body["data"]


def test_sign_in_success():
    """Successful login returns the standardized response envelope."""
    email = "login_user@example.com"
    password = "StrongPassword123!"

    sign_up_response = client.post(
        "/auth/sign-up",
        json={
            "email": email,
            "password": password,
            "first_name": "John",
            "last_name": "Doe",
            "second_name": "Smith",
        },
    )
    assert sign_up_response.status_code == 201

    response = client.post(
        "/auth/sign-in",
        json={"email": email, "password": password},
    )

    assert response.status_code == 202

    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Login successful"
    assert body["data"] is None
    assert "station" in response.cookies


def test_sign_in_invalid_credentials():
    """Invalid credentials return an unauthorized response."""
    response = client.post(
        "/auth/sign-in",
        json={
            "email": "missing_user@example.com",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401

    body = response.json()
    assert body["success"] is False
    assert isinstance(body["message"], str)
    assert body["data"] is None


def test_sign_out_success():
    """Sign-out returns the standardized response and clears the cookie."""
    response = client.post("/auth/sign-out")

    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Logout successful, session terminated"
    assert body["data"] is None

    assert "station" in response.headers.get("set-cookie", "")
    assert "Max-Age=0" in response.headers.get("set-cookie", "")


def test_get_current_user_unauthorized():
    """The profile endpoint rejects unauthenticated requests."""
    response = client.get("/auth/me")

    assert response.status_code == 401

    body = response.json()
    assert body["success"] is False
    assert isinstance(body["message"], str)
    assert body["data"] is None


def test_get_current_user_success():
    """The profile endpoint returns user information inside data."""
    email = "profile_user@example.com"
    password = "StrongPassword123!"

    sign_up_response = client.post(
        "/auth/sign-up",
        json={
            "email": email,
            "password": password,
            "first_name": "John",
            "last_name": "Doe",
            "second_name": "Smith",
        },
    )
    assert sign_up_response.status_code == 201

    response = client.get(
        "/auth/me",
        cookies=sign_up_response.cookies,
    )

    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    assert body["message"] == "User info retrieved successfully"
    assert body["data"]["email"] == email
    assert body["data"]["first_name"] == "John"
    assert body["data"]["last_name"] == "Doe"
    assert body["data"]["second_name"] == "Smith"
    assert body["data"]["roles"] == ["user"]


@pytest.mark.parametrize(
    ("endpoint", "payload"),
    [
        (
                "/auth/sign-up",
                {
                    "email": "invalid-email",
                    "password": "StrongPassword123!",
                    "first_name": "John",
                    "last_name": "Doe",
                    "second_name": "Smith",
                },
        ),
        (
                "/auth/sign-in",
                {
                    "email": "invalid-email",
                    "password": "StrongPassword123!",
                },
        ),
    ],
)
def test_auth_validation_error_uses_standard_envelope(endpoint, payload):
    """Invalid request data uses the same error response structure."""
    response = client.post(endpoint, json=payload)

    assert response.status_code == 422

    body = response.json()
    assert body["success"] is False
    assert body["message"] == "Validation error"
    assert isinstance(body["data"], list)
    assert body["data"]


def test_sign_up_success_message_ukrainian():
    """Registration success message is translated into Ukrainian."""
    response = client.post(
        "/auth/sign-up",
        headers={"Accept-Language": "uk"},
        json={
            "email": "uk_signup@example.com",
            "password": "StrongPassword123!",
            "first_name": "Ivan",
            "last_name": "Petrenko",
            "second_name": "Ivanovych",
        },
    )

    assert response.status_code == 201

    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Реєстрація успішна"


def test_sign_up_success_message_english():
    """Registration success message is translated into English."""
    response = client.post(
        "/auth/sign-up",
        headers={"Accept-Language": "en"},
        json={
            "email": "en_signup@example.com",
            "password": "StrongPassword123!",
            "first_name": "John",
            "last_name": "Doe",
            "second_name": "Smith",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Registration successful"


def test_sign_in_success_message_ukrainian():
    """Login success message is translated into Ukrainian."""
    email = "uk_login@example.com"
    password = "StrongPassword123!"

    client.post(
        "/auth/sign-up",
        headers={"Accept-Language": "uk"},
        json={
            "email": email,
            "password": password,
            "first_name": "Ivan",
            "last_name": "Petrenko",
            "second_name": "Ivanovych",
        },
    )

    response = client.post(
        "/auth/sign-in",
        headers={"Accept-Language": "uk"},
        json={"email": email, "password": password},
    )

    assert response.status_code == 202
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Вхід успішний"


def test_sign_out_success_message_ukrainian():
    """Logout success message is translated into Ukrainian."""
    response = client.post(
        "/auth/sign-out",
        headers={"Accept-Language": "uk"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Вихід успішний, сесія завершена"


def test_get_current_user_success_message_ukrainian():
    """Profile success message is translated into Ukrainian."""
    email = "uk_profile@example.com"
    password = "StrongPassword123!"

    sign_up_response = client.post(
        "/auth/sign-up",
        headers={"Accept-Language": "uk"},
        json={
            "email": email,
            "password": password,
            "first_name": "Ivan",
            "last_name": "Petrenko",
            "second_name": "Ivanovych",
        },
    )

    response = client.get(
        "/auth/me",
        headers={"Accept-Language": "uk"},
        cookies=sign_up_response.cookies,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Інформація про користувача отримана успішно"
