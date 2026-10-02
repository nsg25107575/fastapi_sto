import bcrypt


def get_password_hash(password: str) -> str:
    """
    Generates a secure hash (salt + hash) for storage in the database during registration.
    :param password: str
    """
    # 1. Convert the password string to bytes
    password_bytes = password.encode('utf-8')
    # 2. Generate a salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)

    # 3. Return the string for saving to the database
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Checks whether the entered plaintext password matches the hash from the database.
    :param plain_password: str
    :param hashed_password: str
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False
