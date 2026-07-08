"""Request dependencies: current-user extraction and role enforcement (§2).

Roles form a hierarchy (user < reviewer < admin), matching the capability
table in §2 where every reviewer permission is also granted to admins.
Roles are re-read from the database on every request — never trusted from
the token alone — so a role change or deactivation applies immediately.
"""

import uuid
from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User, UserRole
from app.core.db import get_db_session
from app.core.errors import PermissionDeniedError, UnauthorizedError
from app.core.security import decode_token

_ROLE_LEVEL = {UserRole.user: 0, UserRole.reviewer: 1, UserRole.admin: 2}


async def get_current_user(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise UnauthorizedError("Not authenticated.", code="NOT_AUTHENTICATED")
    payload = decode_token(token, expected_type="access")
    try:
        user_id = uuid.UUID(str(payload.get("sub")))
    except ValueError as exc:
        raise UnauthorizedError("Invalid token.") from exc
    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("Not authenticated.", code="NOT_AUTHENTICATED")
    return user


def require_role(minimum: UserRole | str) -> Callable[[User], Awaitable[User]]:
    minimum_role = UserRole(minimum)

    async def dependency(user: Annotated[User, Depends(get_current_user)]) -> User:
        if _ROLE_LEVEL[user.role] < _ROLE_LEVEL[minimum_role]:
            raise PermissionDeniedError("Your role does not allow this action.")
        return user

    return dependency
