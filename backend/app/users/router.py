"""Admin user-management endpoints (§4.2)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import client_ip
from app.auth.dependencies import require_role
from app.auth.models import User
from app.core.db import get_db_session
from app.users import service
from app.users.schemas import AdminUserListOut, AdminUserOut, AdminUserPatch

router = APIRouter(prefix="/api/v1/admin/users", tags=["admin"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]
Admin = Annotated[User, Depends(require_role("admin"))]


@router.get("")
async def list_users(
    admin: Admin,
    session: DbSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AdminUserListOut:
    users, total = await service.list_users(session, limit=limit, offset=offset)
    return AdminUserListOut(
        items=[AdminUserOut.model_validate(u, from_attributes=True) for u in users],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.patch("/{user_id}")
async def update_user(
    user_id: uuid.UUID,
    body: AdminUserPatch,
    request: Request,
    admin: Admin,
    session: DbSession,
) -> AdminUserOut:
    user = await service.update_user(
        session,
        admin=admin,
        user_id=user_id,
        role=body.role,
        is_active=body.is_active,
        ip=client_ip(request),
    )
    return AdminUserOut.model_validate(user, from_attributes=True)
