import re

from pydantic import BaseModel, Field, field_validator, EmailStr

from i18n.dependency_translator import t


def _validate_password_strength(value: str) -> str:
    """Shared password-strength check used by both create and update schemas."""
    if not re.search(r"\d", value):
        raise ValueError(t("validation.password_requires_digit"))
    if not re.search(r"[A-Z]", value):
        raise ValueError(t("validation.password_requires_uppercase"))
    if not re.search(r"[a-z]", value):
        raise ValueError(t("validation.password_requires_lowercase"))
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
        raise ValueError(t("validation.password_requires_special_char"))
    return value


def _validate_name_field(value: str) -> str:
    """Shared name-field check (empty/whitespace + allowed characters) used by
    both create and update schemas. Does NOT handle the None-passthrough or
    capitalization - callers do that themselves."""
    if len(value) == 0:
        raise ValueError(t("validation.field_empty"))

    name_regex = r"^[a-zA-Zа-яА-Яіїєґ#'’`\s-]+$"

    if not re.match(name_regex, value):
        raise ValueError(t("validation.name_invalid_chars"))

    return value


class UserCreateSchema(BaseModel):
    email: EmailStr
    # base password validations
    password: str = Field(..., min_length=8, max_length=64)
    first_name: str | None = Field(default=None, max_length=50)
    second_name: str | None = Field(default=None, max_length=50)
    last_name: str | None = Field(default=None, max_length=50)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        return _validate_password_strength(value)

    @field_validator("first_name", "second_name", "last_name")
    @classmethod
    def validate_name_fields(cls, value: str | None) -> str | None:
        if value is None:
            return value

        value = value.strip()

        value = _validate_name_field(value)

        if "-" in value:
            value = "-".join(part.capitalize() for part in value.split("-"))
        else:
            value = value.capitalize()

        return value


class UserUpdateSchema(BaseModel):
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=64)
    first_name: str | None = Field(default=None, max_length=50)
    second_name: str | None = Field(default=None, max_length=50)
    last_name: str | None = Field(default=None, max_length=50)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str | None) -> str | None:
        if value is None:
            return value

        return _validate_password_strength(value)

    @field_validator("first_name", "second_name", "last_name")
    @classmethod
    def validate_name_fields(cls, value: str | None) -> str | None:
        if value is None:
            return value

        value = value.strip()

        value = _validate_name_field(value)

        if "-" in value:
            value = "-".join(part.capitalize() for part in value.split("-"))
        else:
            value = value.capitalize()

        return value


class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=64)
