"""Unit tests for auth/password.py (bcrypt hashing helpers)."""
from auth.password import get_password_hash, verify_password


def test_get_password_hash_returns_different_value_than_plaintext():
    hashed = get_password_hash("StrongPass1!")

    assert hashed != "StrongPass1!"
    assert isinstance(hashed, str)
    assert len(hashed) > 0


def test_get_password_hash_is_salted_and_non_deterministic():
    hashed_a = get_password_hash("StrongPass1!")
    hashed_b = get_password_hash("StrongPass1!")

    # bcrypt generates a fresh random salt each call, so two hashes of the
    # same plaintext must differ.
    assert hashed_a != hashed_b


def test_verify_password_accepts_correct_password():
    hashed = get_password_hash("StrongPass1!")

    assert verify_password("StrongPass1!", hashed) is True


def test_verify_password_rejects_incorrect_password():
    hashed = get_password_hash("StrongPass1!")

    assert verify_password("WrongPass1!", hashed) is False


def test_verify_password_returns_false_on_malformed_hash():
    # Should not raise — malformed/garbage hashes must be treated as a
    # failed verification, not an exception.
    assert verify_password("whatever", "not-a-real-bcrypt-hash") is False


def test_verify_password_empty_strings_do_not_raise():
    assert verify_password("", "") is False
