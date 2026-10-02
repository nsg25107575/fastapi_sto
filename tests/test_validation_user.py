"""Unit tests for validations/user.py — password strength & name validators."""
import pytest
from pydantic import ValidationError

from validations.user import UserCreateSchema, UserUpdateSchema, UserLoginSchema

VALID_PAYLOAD = {
    "email": "person@example.com",
    "password": "StrongPass1!",
    "first_name": "john",
    "second_name": None,
    "last_name": "doe",
}


def test_user_create_schema_accepts_valid_payload():
    schema = UserCreateSchema(**VALID_PAYLOAD)

    assert schema.email == "person@example.com"
    # Name fields get auto-capitalized by the validator.
    assert schema.first_name == "John"
    assert schema.last_name == "Doe"


@pytest.mark.parametrize(
    "password, reason",
    [
        ("short1!", "too short"),
        ("alllowercase1!", "missing uppercase"),
        ("ALLUPPERCASE1!", "missing lowercase"),
        ("NoDigitsHere!", "missing digit"),
        ("NoSpecialChar1", "missing special character"),
    ],
)
def test_user_create_schema_rejects_weak_passwords(password, reason):
    payload = {**VALID_PAYLOAD, "password": password}

    with pytest.raises(ValidationError):
        UserCreateSchema(**payload)


def test_user_create_schema_rejects_invalid_email():
    payload = {**VALID_PAYLOAD, "email": "not-an-email"}

    with pytest.raises(ValidationError):
        UserCreateSchema(**payload)


@pytest.mark.parametrize("bad_name", ["", "   ", "John123", "John@Doe"])
def test_user_create_schema_rejects_invalid_name(bad_name):
    payload = {**VALID_PAYLOAD, "first_name": bad_name}

    with pytest.raises(ValidationError):
        UserCreateSchema(**payload)


def test_user_create_schema_capitalizes_hyphenated_name():
    payload = {**VALID_PAYLOAD, "first_name": "anna-maria"}

    schema = UserCreateSchema(**payload)

    assert schema.first_name == "Anna-Maria"


def test_user_create_schema_allows_none_optional_names():
    payload = {**VALID_PAYLOAD, "first_name": None, "second_name": None, "last_name": None}

    schema = UserCreateSchema(**payload)

    assert schema.first_name is None


def test_user_update_schema_allows_all_fields_omitted():
    schema = UserUpdateSchema()

    assert schema.email is None
    assert schema.password is None


def test_user_update_schema_validates_password_when_present():
    with pytest.raises(ValidationError):
        UserUpdateSchema(password="weak")


def test_user_login_schema_requires_email_and_password():
    with pytest.raises(ValidationError):
        UserLoginSchema(email="person@example.com")

    schema = UserLoginSchema(email="person@example.com", password="StrongPass1!")

    assert schema.email == "person@example.com"


@pytest.mark.parametrize(
    "password, reason",
    [
        ("short1!", "too short"),
        ("alllowercase1!", "missing uppercase"),
        ("ALLUPPERCASE1!", "missing lowercase"),
        ("NoDigitsHere!", "missing digit"),
        ("NoSpecialChar1", "missing special character"),
    ],
)
def test_user_update_schema_rejects_weak_passwords_when_provided(password, reason):
    with pytest.raises(ValidationError):
        UserUpdateSchema(password=password)


def test_user_update_schema_accepts_strong_password():
    schema = UserUpdateSchema(password="StrongPass1!")

    assert schema.password == "StrongPass1!"


@pytest.mark.parametrize("bad_name", ["", "   ", "John123", "John@Doe"])
def test_user_update_schema_rejects_invalid_name(bad_name):
    with pytest.raises(ValidationError):
        UserUpdateSchema(first_name=bad_name)


def test_user_update_schema_formats_valid_name():
    schema = UserUpdateSchema(first_name="anna-maria")

    assert schema.first_name == "Anna-Maria"


def test_user_update_schema_allows_none_name_fields():
    schema = UserUpdateSchema(first_name=None, second_name=None, last_name=None)

    assert schema.first_name is None
    assert schema.second_name is None
    assert schema.last_name is None
