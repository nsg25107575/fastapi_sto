from database import SessionLocal
from models.user import UserModel
from auth.password import hash_password


def create_user():
    session = SessionLocal()

    try:
        user = UserModel(
            email="admin@example.com",
            password=hash_password("admin123"),
            first_name="Admin",
            second_name=None,
            last_name=None,
        )

        session.add(user)
        session.commit()
        session.refresh(user)

        print(f"User created: id={user.id}, email={user.email}")

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


if __name__ == "__main__":
    create_user()
