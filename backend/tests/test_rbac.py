"""RBAC dependency tests, parameterised across roles × protected endpoints (§10).

Real protected routes arrive with later tasks; these tests mount one route
per role level to prove the `get_current_user` / `require_role` dependencies
enforce the §2 hierarchy (user < reviewer < admin).
"""

import os
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt as pyjwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user, require_role
from app.auth.models import User
from app.main import create_app
from tests.conftest import set_user_role


def _protected_app() -> FastAPI:
    app = create_app()

    @app.get("/protected/user")
    def user_route(user: Annotated[User, Depends(get_current_user)]) -> dict[str, str]:
        return {"email": user.email}

    @app.get("/protected/reviewer")
    def reviewer_route(user: Annotated[User, Depends(require_role("reviewer"))]) -> dict[str, str]:
        return {"email": user.email}

    @app.get("/protected/admin")
    def admin_route(user: Annotated[User, Depends(require_role("admin"))]) -> dict[str, str]:
        return {"email": user.email}

    return app


def _token_for(client: TestClient, role: str) -> str:
    email = f"{role}@example.com"
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "sufficiently long 1", "fullName": f"Test {role}"},
    )
    assert response.status_code == 201, response.text
    set_user_role(email, role)
    login = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "sufficiently long 1"}
    )
    token: str = login.json()["accessToken"]
    return token


@pytest.fixture
def protected_client() -> TestClient:
    return TestClient(_protected_app())


@pytest.mark.parametrize(
    ("role", "endpoint", "expected"),
    [
        ("user", "/protected/user", 200),
        ("user", "/protected/reviewer", 403),
        ("user", "/protected/admin", 403),
        ("reviewer", "/protected/user", 200),
        ("reviewer", "/protected/reviewer", 200),
        ("reviewer", "/protected/admin", 403),
        ("admin", "/protected/user", 200),
        ("admin", "/protected/reviewer", 200),
        ("admin", "/protected/admin", 200),
    ],
)
def test_role_matrix(protected_client: TestClient, role: str, endpoint: str, expected: int) -> None:
    token = _token_for(protected_client, role)
    response = protected_client.get(endpoint, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == expected, response.text
    if expected == 403:
        assert response.json()["error"]["code"] == "PERMISSION_DENIED"


def test_missing_token_is_401(protected_client: TestClient) -> None:
    response = protected_client.get("/protected/user")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"


def test_garbage_token_is_401(protected_client: TestClient) -> None:
    response = protected_client.get(
        "/protected/user", headers={"Authorization": "Bearer garbage"}
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_expired_token_is_401(protected_client: TestClient) -> None:
    expired = pyjwt.encode(
        {
            "sub": "00000000-0000-0000-0000-000000000000",
            "role": "user",
            "type": "access",
            "exp": datetime.now(UTC) - timedelta(minutes=1),
        },
        os.environ["JWT_SECRET"],
        algorithm="HS256",
    )
    response = protected_client.get(
        "/protected/user", headers={"Authorization": f"Bearer {expired}"}
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "TOKEN_EXPIRED"


def test_refresh_token_rejected_as_access_token(protected_client: TestClient) -> None:
    _token_for(protected_client, "user")
    refresh_cookie = protected_client.cookies["refresh_token"]
    response = protected_client.get(
        "/protected/user", headers={"Authorization": f"Bearer {refresh_cookie}"}
    )
    assert response.status_code == 401
