import re

from pydantic import BaseModel, Field, field_validator, EmailStr


class UserCreateSchema(BaseModel):
    email: EmailStr
    # base password validation
    password: str = Field(..., min_length=8, max_length=64)
    first_name: str | None = Field(default=None, max_length=50)
    second_name: str | None = Field(default=None, max_length=50)
    last_name: str | None = Field(default=None, max_length=50)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        # Check for the presence of at least one digit
        if not re.search(r"\d", value):
            raise ValueError("The password must contain at least one digit.")
        # Check for the presence of at least one uppercase letter
        if not re.search(r"[A-Z]", value):
            raise ValueError("The password must contain at least one uppercase letter.")
        # Check for the presence of at least one lowercase letter
        if not re.search(r"[a-z]", value):
            raise ValueError("The password must contain at least one lowercase letter.")
        # Check for special characters (optional, but recommended for security)
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError("The password must contain at least one special character (!@#$%^&*, etc.).")

        return value

    @field_validator("first_name", "second_name", "last_name")
    @classmethod
    def validate_name_fields(cls, value: str | None) -> str | None:
        if value is None:
            return value

        # Remove extra spaces from the beginning and end
        value = value.strip()

        # Check to ensure the string does not become empty after removing whitespace
        if len(value) == 0:
            raise ValueError("The field cannot be empty or consist only of spaces.")

        # Regular expression for validating letters, hyphens, and apostrophes
        name_regex = r"^[a-zA-Zа-яА-ЯіІїЇєЄґҐ#'’`\s-]+$"

        if not re.match(name_regex, value):
            raise ValueError(
                "Only letters, spaces, hyphens, and apostrophes are allowed. Numbers and special characters are prohibited."
            )

        # We format it so that the first letter is automatically capitalized (e.g., "ivan" -> "Ivan").
        # If the name is double-barreled, capitalize each part (e.g., "anna-maria" -> "Anna-Maria").
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

        if not re.search(r"\d", value):
            raise ValueError("The password must contain at least one digit.")

        if not re.search(r"[A-Z]", value):
            raise ValueError("The password must contain at least one uppercase letter.")

        if not re.search(r"[a-z]", value):
            raise ValueError("The password must contain at least one lowercase letter.")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError(
                "The password must contain at least one special character (!@#$%^&*, etc.)."
            )

        return value

    @field_validator("first_name", "second_name", "last_name")
    @classmethod
    def validate_name_fields(cls, value: str | None) -> str | None:
        if value is None:
            return value

        value = value.strip()

        if len(value) == 0:
            raise ValueError("The field cannot be empty or consist only of spaces.")

        name_regex = r"^[a-zA-Zа-яА-ЯіІїЇєЄґҐ#'’`\s-]+$"

        if not re.match(name_regex, value):
            raise ValueError(
                "Only letters, spaces, hyphens, and apostrophes are allowed. "
                "Numbers and special characters are prohibited."
            )

        if "-" in value:
            value = "-".join(part.capitalize() for part in value.split("-"))
        else:
            value = value.capitalize()

        return value


class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=64)
