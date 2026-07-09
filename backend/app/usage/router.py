"""Admin usage/cost endpoint (§4.2)."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_role
from app.auth.models import User
from app.core.db import get_db_session
from app.usage import service
from app.usage.schemas import UsageOut

router = APIRouter(prefix="/api/v1/admin/usage", tags=["admin"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]
Admin = Annotated[User, Depends(require_role("admin"))]


@router.get("")
async def usage_stats(
    admin: Admin,
    session: DbSession,
    group_by: Annotated[Literal["day", "user"], Query(alias="groupBy")] = "day",
) -> UsageOut:
    return await service.usage_stats(session, group_by=group_by)
