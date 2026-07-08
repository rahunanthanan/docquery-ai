"""Auth business logic: registration and credential verification."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.errors import ConflictError, UnauthorizedError
from app.core.security import hash_password, verify_password


async def register_user(
    session: AsyncSession, *, email: str, password: str, full_name: str
) -> User:
    user = User(email=email, password_hash=hash_password(password), full_name=full_name)
    session.add(user)
    try:
        await session.commit()
    except IntegrityError as exc:
        # citext unique constraint — the atomic source of truth (no pre-check race)
        await session.rollback()
        raise ConflictError(
            "An account with this email already exists.", code="EMAIL_ALREADY_REGISTERED"
        ) from exc
    await session.refresh(user)
    return user


async def authenticate_user(session: AsyncSession, *, email: str, password: str) -> User:
    user = await session.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(password, user.password_hash):
        # same error either way — never reveal whether the email exists
        raise UnauthorizedError("Incorrect email or password.", code="INVALID_CREDENTIALS")
    if not user.is_active:
        raise UnauthorizedError("This account is disabled.", code="ACCOUNT_DISABLED")
    return user
