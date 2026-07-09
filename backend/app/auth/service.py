"""Auth business logic: registration and credential verification."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import log_event
from app.auth.models import User
from app.core.errors import ConflictError, UnauthorizedError
from app.core.security import hash_password, verify_password


async def register_user(
    session: AsyncSession, *, email: str, password: str, full_name: str, ip: str | None = None
) -> User:
    user = User(email=email, password_hash=hash_password(password), full_name=full_name)
    session.add(user)
    try:
        await session.flush()
    except IntegrityError as exc:
        # citext unique constraint — the atomic source of truth (no pre-check race)
        await session.rollback()
        raise ConflictError(
            "An account with this email already exists.", code="EMAIL_ALREADY_REGISTERED"
        ) from exc
    log_event(session, actor=user, action="user.registered", entity_type="user",
              entity_id=user.id, ip=ip)
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate_user(
    session: AsyncSession, *, email: str, password: str, ip: str | None = None
) -> User:
    user = await session.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(password, user.password_hash):
        # same error either way — never reveal whether the email exists
        raise UnauthorizedError("Incorrect email or password.", code="INVALID_CREDENTIALS")
    if not user.is_active:
        raise UnauthorizedError("This account is disabled.", code="ACCOUNT_DISABLED")
    log_event(session, actor=user, action="user.login", entity_type="user",
              entity_id=user.id, ip=ip)
    await session.commit()
    return user
