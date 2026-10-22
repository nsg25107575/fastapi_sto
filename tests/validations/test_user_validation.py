"""
Tests for user validation logic.
"""
import pytest

from i18n.context import reset_current_locale, set_current_locale
from validations.user import _validate_password_strength, _validate_name_field


@pytest.fixture(autouse=True)
def _reset_locale():
    """Restore the current locale after tests that change it."""
    token = set_current_locale("en")
    yield
    reset_current_locale(token)


# --- Unit tests on the shared validator functions directly -----------------

def test_password_without_digit_raises_translated_error():
    with pytest.raises(ValueError, match="must contain at least one digit"):
        _validate_password_strength("NoDigits!")


def test_password_without_uppercase_raises_translated_error():
    with pytest.raises(ValueError, match="uppercase letter"):
        _validate_password_strength("nouppercase1!")


def test_password_without_lowercase_raises_translated_error():
    with pytest.raises(ValueError, match="lowercase letter"):
        _validate_password_strength("NOLOWERCASE1!")


def test_password_without_special_char_raises_translated_error():
    with pytest.raises(ValueError, match="special character"):
        _validate_password_strength("NoSpecial1")


def test_valid_password_passes_through_unchanged():
    assert _validate_password_strength("StrongP@ss1") == "StrongP@ss1"


def test_empty_name_raises_translated_error():
    with pytest.raises(ValueError, match="cannot be empty"):
        _validate_name_field("")


def test_name_with_digits_raises_translated_error():
    with pytest.raises(ValueError, match="hyphens"):
        _validate_name_field("Jo3")


def test_valid_name_passes_through_unchanged():
    assert _validate_name_field("Jo-Ann O'Brien") == "Jo-Ann O'Brien"


def test_password_validation_respects_uk_locale():
    set_current_locale("uk")
    with pytest.raises(ValueError) as exc_info:
        _validate_password_strength("NoDigits!")
    assert "must contain at least one digit" not in str(exc_info.value)


# --- Existing HTTP-level tests (sign-up through the full stack) ------------


def test_sign_up_password_without_digit_returns_translated_error(client):
    """
    Test that signing up with a password that lacks a digit returns an error message in Ukrainian
    when the 'accept-language' header is set to 'uk'.
    """
    response = client.post(
        "/auth/sign-up",
        json={"email": "x@example.com", "password": "NoDigits!", "first_name": "A", "last_name": "B"},
        headers={"accept-language": "uk"},
    )
    assert response.status_code == 422
    messages = [item["message"] for item in response.json()["data"]]
    assert any("must contain at least one digit" not in m for m in messages)  # очікуємо переклад, не en-текст


def test_sign_up_password_without_digit_returns_english_error_by_default(client):
    """
    Test that signing up with a password that lacks a digit returns an error message in English
    when the 'accept-language' header is not set to 'uk'.
    """
    response = client.post(
        "/auth/sign-up",
        json={"email": "y@example.com", "password": "NoDigits!", "first_name": "A", "last_name": "B"},
    )
    assert response.status_code == 422
    messages = [item["message"] for item in response.json()["data"]]
    assert any("must contain at least one digit" in m for m in messages)


def test_sign_up_password_without_uppercase_returns_translated_error(client):
    """
    Test that signing up with a password that lacks an uppercase letter returns an error message in Ukrainian
    when the 'accept-language' header is set to 'uk'.
    """
    response = client.post(
        "/auth/sign-up",
        json={"email": "z@example.com", "password": "nouppercase1!", "first_name": "A", "last_name": "B"},
        headers={"accept-language": "uk"},
    )
    assert response.status_code == 422
    messages = [item["message"] for item in response.json()["data"]]
    assert any("uppercase letter" not in m for m in messages)


def test_sign_up_name_with_invalid_chars_returns_translated_error(client):
    """
    Test that signing up with a name containing invalid characters returns an error message in Ukrainian
    when the 'accept-language' header is set to 'uk'.
    """
    response = client.post(
        "/auth/sign-up",
        json={"email": "w@example.com", "password": "StrongP@ss1", "first_name": "Jo3", "last_name": "Doe"},
        headers={"accept-language": "uk"},
    )
    assert response.status_code == 422
    messages = [item["message"] for item in response.json()["data"]]
    assert any("hyphens" not in m for m in messages)


def test_sign_up_empty_name_returns_translated_error(client):
    """
    Test that signing up with an empty name returns an error message in Ukrainian
    when the 'accept-language' header is set to 'uk'.
    """
    response = client.post(
        "/auth/sign-up",
        json={"email": "v@example.com", "password": "StrongP@ss1", "first_name": "   ", "last_name": "Doe"},
        headers={"accept-language": "uk"},
    )
    assert response.status_code == 422
    messages = [item["message"] for item in response.json()["data"]]
    assert any("cannot be empty" not in m for m in messages)
