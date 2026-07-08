"""Password hashing and JWT issue/verify utilities (requirements §2, §6).

Access tokens (15 min) carry ``sub``, ``role``, ``exp``; refresh tokens
(7 days) are distinguished by a ``type`` claim so one can never be used
in place of the other.
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import bcrypt
import jwt

from app.core.config import get_settings
from app.core.errors import UnauthorizedError

TokenType = Literal["access", "refresh"]

BCRYPT_ROUNDS = 12  # fixed by §6


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_token(*, user_id: uuid.UUID, role: str, token_type: TokenType) -> str:
    settings = get_settings()
    ttl = (
        timedelta(minutes=settings.access_token_ttl_minutes)
        if token_type == "access"
        else timedelta(days=settings.refresh_token_ttl_days)
    )
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": token_type,
        "jti": uuid.uuid4().hex,  # unique per token: rotation always yields a new token
        "iat": now,
        "exp": now + ttl,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str, *, expected_type: TokenType) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload: dict[str, Any] = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError("Token has expired.", code="TOKEN_EXPIRED") from exc
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError("Invalid token.") from exc
    if payload.get("type") != expected_type:
        raise UnauthorizedError("Invalid token.")
    return payload
