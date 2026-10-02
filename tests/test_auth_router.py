"""Tests for /auth/sign-up, /auth/sign-in, /auth/sign-out, /auth/me."""
import uuid


def _unique_email():
    return f"user-{uuid.uuid4().hex[:8]}@example.com"


def test_sign_up_creates_user_and_sets_cookie(client):
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
    response = client.post(
        "/auth/sign-in",
        json={"email": _unique_email(), "password": "StrongPass1!"},
    )

    assert response.status_code == 401


def test_me_requires_authentication(client):
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_me_returns_current_user_profile(auth_client):
    client, user_payload = auth_client

    response = client.get("/auth/me")

    assert response.status_code == 200
    detail = response.json()["detail"][0]
    assert detail["email"] == user_payload["email"]


def test_sign_out_invalidates_session(auth_client):
    client, _user_payload = auth_client

    me_before = client.get("/auth/me")
    assert me_before.status_code == 200

    sign_out = client.post("/auth/sign-out")
    assert sign_out.status_code == 200

    me_after = client.get("/auth/me")
    assert me_after.status_code == 401
