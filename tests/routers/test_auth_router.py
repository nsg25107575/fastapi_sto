"""Tests for /auth/sign-up, /auth/sign-in, /auth/sign-out, /auth/me."""
import uuid


def _unique_email() -> str:
    """
    Generate a unique email address for testing purposes. The email will be in the format "user-<random_hex>@example.com".
    Returns:
        str: A unique email address.
    """
    return f"user-{uuid.uuid4().hex[:8]}@example.com"


def test_sign_up_creates_user_and_sets_cookie(client) -> None:
    """
    Test that signing up a new user creates the user and sets the session cookie.
    Args:
        client: The test client used to make requests to the application.
    """
    email = _unique_email()

    response = client.post(
        "/auth/sign-up",
        json={
            "email": email,
            "password": "StrongPass1!",
            "first_name": "New",
            "last_name": "User",
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    detail = body["detail"][0]
    assert detail["type"] == "success"
    assert "id" in detail
    assert "station" in response.cookies


def test_sign_up_rejects_duplicate_email(client):
    """
    Test that signing up with a duplicate email address returns a 409 Conflict status code.
    Args:
        client: The test client used to make requests to the application.
    """
    email = _unique_email()
    payload = {
        "email": email,
        "password": "StrongPass1!",
        "first_name": "Dup",
        "last_name": "User",
    }

    first = client.post("/auth/sign-up", json=payload)
    assert first.status_code == 201

    second = client.post("/auth/sign-up", json=payload)
    assert second.status_code == 409


def test_sign_up_rejects_weak_password(client):
    """
    Test that signing up with a weak password returns a 422 Unprocessable Entity status code.
    Args:
        client: The test client used to make requests to the application.
    """
    response = client.post(
        "/auth/sign-up",
        json={
            "email": _unique_email(),
            "password": "weak",
            "first_name": "Weak",
            "last_name": "User",
        },
    )

    assert response.status_code == 422


def test_sign_in_with_correct_credentials(client):
    """
    Test that signing in with correct credentials returns a 202 Accepted status code and sets the session cookie.
    Args:
        client: The test client used to make requests to the application.
    """
    email = _unique_email()
    client.post(
        "/auth/sign-up",
        json={
            "email": email,
            "password": "StrongPass1!",
            "first_name": "Login",
            "last_name": "User",
        },
    )

    response = client.post(
        "/auth/sign-in",
        json={"email": email, "password": "StrongPass1!"},
    )

    assert response.status_code == 202
    assert "station" in response.cookies


def test_sign_in_with_wrong_password_returns_401(client):
    """
    Test that signing in with a wrong password returns a 401 Unauthorized status code.
    Args:
        client: The test client used to make requests to the application.
    """
    email = _unique_email()
    client.post(
        "/auth/sign-up",
        json={
            "email": email,
            "password": "StrongPass1!",
            "first_name": "Login",
            "last_name": "User",
        },
    )

    response = client.post(
        "/auth/sign-in",
        json={"email": email, "password": "WrongPass1!"},
    )

    assert response.status_code == 401


def test_sign_in_with_unknown_email_returns_401(client):
    """
    Test that signing in with an unknown email returns a 401 Unauthorized status code.
    Args:
        client: The test client used to make requests to the application.
    """
    response = client.post(
        "/auth/sign-in",
        json={"email": _unique_email(), "password": "StrongPass1!"},
    )

    assert response.status_code == 401


def test_me_requires_authentication(client):
    """
    Test that the /auth/me endpoint requires authentication and returns a 401 Unauthorized status code
    when accessed without a valid session.
    Args:
        client: The test client used to make requests to the application.
    """
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_me_returns_current_user_profile(auth_client):
    """
    Test that the /auth/me endpoint returns the profile of the currently authenticated user.
    Args:
        auth_client: A fixture that provides an authenticated client and the user payload.
    """
    client, user_payload = auth_client

    response = client.get("/auth/me")

    assert response.status_code == 200
    detail = response.json()["detail"][0]
    assert detail["email"] == user_payload["email"]


def test_sign_out_invalidates_session(auth_client):
    """
    Test that signing out invalidates the session and prevents access to the /auth/me endpoint.
    Args:
        auth_client: A fixture that provides an authenticated client and the user payload.
    """
    client, _user_payload = auth_client

    me_before = client.get("/auth/me")
    assert me_before.status_code == 200

    sign_out = client.post("/auth/sign-out")
    assert sign_out.status_code == 200

    me_after = client.get("/auth/me")
    assert me_after.status_code == 401


def test_sign_up_returns_translated_success_message(client):
    """
    Test that the sign-up endpoint returns a translated success message
    when the Accept-Language header is set to 'uk' (Ukrainian).
    """
    response = client.post(
        "/auth/sign-up",
        json={"email": "new_user@example.com", "password": "StrongP@ss1", "first_name": "A", "last_name": "B"},
        headers={"accept-language": "uk"},
    )
    assert response.status_code == 201
    msg = response.json()["detail"][0]["msg"]
    assert msg != "Registration successful"  # awaiting translation; no en-fallback.


def test_sign_up_returns_english_success_message_by_default(client):
    """
    Test that the sign-up endpoint returns an English success message
    when the Accept-Language header is not set or is set to 'en'.
    """
    response = client.post(
        "/auth/sign-up",
        json={"email": "another_user@example.com", "password": "StrongP@ss1", "first_name": "A", "last_name": "B"},
    )
    assert response.status_code == 201
    assert response.json()["detail"][0]["msg"] == "Registration successful"


def test_sign_in_returns_translated_success_message(auth_client):
    """
    Test that the sign-in endpoint returns a translated success message
    when the Accept-Language header is set to 'uk' (Ukrainian).
    """
    client, _user_payload = auth_client

    response = client.post(
        "/auth/sign-in",
        json={"email": _user_payload["email"], "password": "StrongPass1!"},
        headers={"accept-language": "uk"},
    )
    assert response.status_code == 202
    assert response.json()["detail"][0]["msg"] != "Login successful"


def test_sign_out_returns_translated_success_message(auth_client):
    """
    Test that the sign-out endpoint returns a translated success message
    when the Accept-Language header is set to 'uk' (Ukrainian).
    """
    client, _user_payload = auth_client

    response = client.post("/auth/sign-out", headers={"accept-language": "uk"})
    assert response.status_code == 200
    assert response.json()["detail"][0]["msg"] != "Logout successful, session terminated"


def test_get_current_user_returns_translated_success_message(auth_client):
    """
    Test that the /auth/me endpoint returns a translated success message
    when the Accept-Language header is set to 'uk' (Ukrainian).
    """
    client, _user_payload = auth_client

    response = client.get("/auth/me", headers={"accept-language": "uk"})
    assert response.status_code == 200
    assert response.json()["detail"][0]["msg"] != "User info retrieved successfully"
