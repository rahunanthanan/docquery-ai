"""Auth endpoints: register, login, refresh (§4.2).

The refresh token never appears in a response body — it lives in an
httpOnly cookie scoped to /api/v1/auth and is rotated on every refresh.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import client_ip
from app.auth import service
from app.auth.models import User
from app.auth.schemas import LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.core.config import get_settings
from app.core.db import get_db_session
from app.core.errors import UnauthorizedError
from app.core.security import create_token, decode_token

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

REFRESH_COOKIE = "refresh_token"

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


def _token_response(user: User, response: Response) -> TokenResponse:
    settings = get_settings()
    access = create_token(user_id=user.id, role=user.role.value, token_type="access")
    refresh = create_token(user_id=user.id, role=user.role.value, token_type="refresh")
    response.set_cookie(
        REFRESH_COOKIE,
        refresh,
        max_age=settings.refresh_token_ttl_days * 24 * 3600,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        path="/api/v1/auth",
    )
    return TokenResponse(
        access_token=access,
        expires_in=settings.access_token_ttl_minutes * 60,
        user=UserOut.model_validate(user),
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, request: Request, session: DbSession) -> UserOut:
    user = await service.register_user(
        session,
        email=body.email,
        password=body.password,
        full_name=body.full_name,
        ip=client_ip(request),
    )
    return UserOut.model_validate(user)


@router.post("/login")
async def login(
    body: LoginRequest, request: Request, response: Response, session: DbSession
) -> TokenResponse:
    user = await service.authenticate_user(
        session, email=body.email, password=body.password, ip=client_ip(request)
    )
    return _token_response(user, response)


@router.post("/refresh")
async def refresh(request: Request, response: Response, session: DbSession) -> TokenResponse:
    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        raise UnauthorizedError("Not authenticated.", code="NOT_AUTHENTICATED")
    payload = decode_token(token, expected_type="refresh")
    try:
        user_id = uuid.UUID(str(payload.get("sub")))
    except ValueError as exc:
        raise UnauthorizedError("Invalid token.") from exc
    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("Not authenticated.", code="NOT_AUTHENTICATED")
    return _token_response(user, response)
