"""Seeder for fake user data."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from auth.password import get_password_hash
from models import UserModel
from seeders.base import Seeder


class FakeUsersSeeder(Seeder):
    users = (
        ("fake_user@example.com", "adm123456", "fake", "user"),
    )

    def run(self, session: Session) -> None:
        """Create fake users"""
        existing_users = set(session.scalars(select(UserModel.email)).all())
        session.add_all(
            UserModel(
                email=email,
                password=get_password_hash(password),
                first_name=first_name,
                last_name=last_name
            )
            for email, password, first_name, last_name in self.users
            if email not in existing_users
        )
        session.flush()
