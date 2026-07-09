"""Admin user management (§2, §4.2) with §8 audit writes."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import log_event
from app.auth.models import User, UserRole
from app.core.errors import NotFoundError, ValidationFailed


async def list_users(
    session: AsyncSession, *, limit: int, offset: int
) -> tuple[list[User], int]:
    total = await session.scalar(select(func.count()).select_from(User))
    users = await session.scalars(
        select(User).order_by(User.created_at, User.id).limit(limit).offset(offset)
    )
    return list(users), total or 0


async def update_user(
    session: AsyncSession,
    *,
    admin: User,
    user_id: uuid.UUID,
    role: UserRole | None,
    is_active: bool | None,
    ip: str | None,
) -> User:
    if user_id == admin.id:
        # an admin locking themselves out is unrecoverable in-app
        raise ValidationFailed(
            "Admins cannot change their own role or active status.",
            code="CANNOT_MODIFY_SELF",
        )
    target = await session.get(User, user_id)
    if target is None:
        raise NotFoundError("User not found.", code="USER_NOT_FOUND")

    if role is not None and role != target.role:
        log_event(
            session,
            actor=admin,
            action="user.role_changed",
            entity_type="user",
            entity_id=target.id,
            metadata={"old_role": target.role.value, "new_role": role.value},
            ip=ip,
        )
        target.role = role
    if is_active is not None and is_active != target.is_active:
        log_event(
            session,
            actor=admin,
            action="user.deactivated" if not is_active else "user.reactivated",
            entity_type="user",
            entity_id=target.id,
            ip=ip,
        )
        target.is_active = is_active

    await session.commit()
    await session.refresh(target)
    return target
