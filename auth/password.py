from passlib.context import CryptContext

# Context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """
    Generates a secure hash (salt + hash) for storage in the database during registration.
    :param password: str
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Checks whether the entered plaintext password matches the hash from the database.
    :param plain_password: str
    :param hashed_password: str
    """
    return pwd_context.verify(plain_password, hashed_password)
