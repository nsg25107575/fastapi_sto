from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

from config import Config


def create_access_token(
        user_id: str,
        roles: list[str] | None = None
) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        # ID користувача
        "sub": user_id,
        # Час видачі токена
        "iat": now,
        # Час завершення терміну дії токена
        "exp": now + timedelta(
            minutes=Config.token_expiration_minutes
        ),
        # Ролі користувача
        "roles": roles or ["user"],
    }

    encoded_jwt = jwt.encode(
        payload,
        Config.jwt_secret_key,
        algorithm=Config.jwt_algorithm,
    )

    return encoded_jwt


def verify_access_token(token: str) -> Optional[dict]:
    try:
        decoded_payload = jwt.decode(
            token,
            Config.jwt_secret_key,
            algorithms=[Config.jwt_algorithm],
        )

        return decoded_payload

    except jwt.ExpiredSignatureError:
        print("Error: The token has expired.")
        return None

    except jwt.InvalidTokenError:
        print("Error: Invalid token payload or signature.")
        return None
