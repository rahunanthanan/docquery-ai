"""Auth flow tests: register, login, refresh (requirements §2, §4.2, §6)."""

import pytest
from fastapi.testclient import TestClient

VALID_REGISTER = {
    "email": "ada@example.com",
    "password": "correct horse 9",
    "fullName": "Ada Lovelace",
}


def _register(client: TestClient, **overrides: str) -> dict[str, str]:
    body = {**VALID_REGISTER, **overrides}
    response = client.post("/api/v1/auth/register", json=body)
    assert response.status_code == 201, response.text
    result: dict[str, str] = response.json()
    return result


# ── register ──────────────────────────────────────────────────────────────


def test_register_creates_user_with_default_role(client: TestClient) -> None:
    body = _register(client)
    assert body["email"] == "ada@example.com"
    assert body["fullName"] == "Ada Lovelace"
    assert body["role"] == "user"
    assert body["isActive"] is True
    assert "password" not in str(body).lower()  # no hash, no plaintext, ever


def test_register_duplicate_email_conflicts(client: TestClient) -> None:
    _register(client)
    response = client.post("/api/v1/auth/register", json=VALID_REGISTER)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EMAIL_ALREADY_REGISTERED"


def test_register_email_uniqueness_is_case_insensitive(client: TestClient) -> None:
    _register(client)
    response = client.post(
        "/api/v1/auth/register", json={**VALID_REGISTER, "email": "ADA@example.com"}
    )
    assert response.status_code == 409


@pytest.mark.parametrize(
    "password",
    [
        "short1a",  # < 10 chars
        "onlyletters",  # no digit
        "1234567890",  # no letter
    ],
)
def test_register_rejects_weak_passwords(client: TestClient, password: str) -> None:
    response = client.post("/api/v1/auth/register", json={**VALID_REGISTER, "password": password})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_FAILED"


def test_register_rejects_invalid_email(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register", json={**VALID_REGISTER, "email": "not-an-email"}
    )
    assert response.status_code == 422


# ── login ─────────────────────────────────────────────────────────────────


def test_login_returns_access_token_and_refresh_cookie(client: TestClient) -> None:
    _register(client)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": VALID_REGISTER["email"], "password": VALID_REGISTER["password"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["tokenType"] == "bearer"
    assert body["expiresIn"] == 15 * 60
    assert body["accessToken"]
    assert body["user"]["email"] == VALID_REGISTER["email"]

    set_cookie = response.headers["set-cookie"]
    assert "refresh_token=" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "Path=/api/v1/auth" in set_cookie
    assert body["accessToken"] not in set_cookie  # cookie carries refresh, not access


def test_login_wrong_password_is_401(client: TestClient) -> None:
    _register(client)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": VALID_REGISTER["email"], "password": "wrong password 1"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_unknown_email_same_error_as_wrong_password(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login", json={"email": "ghost@example.com", "password": "whatever pass 1"}
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


# ── refresh ───────────────────────────────────────────────────────────────


def test_refresh_rotates_tokens(client: TestClient) -> None:
    _register(client)
    login = client.post(
        "/api/v1/auth/login",
        json={"email": VALID_REGISTER["email"], "password": VALID_REGISTER["password"]},
    )
    old_cookie = client.cookies["refresh_token"]

    response = client.post("/api/v1/auth/refresh")  # cookie sent automatically
    assert response.status_code == 200
    body = response.json()
    assert body["accessToken"]
    assert body["user"]["email"] == VALID_REGISTER["email"]
    assert "refresh_token=" in response.headers["set-cookie"]  # rotated
    assert client.cookies["refresh_token"] != old_cookie
    assert login.json()["accessToken"] != body["accessToken"]


def test_refresh_without_cookie_is_401(client: TestClient) -> None:
    response = client.post("/api/v1/auth/refresh")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"


def test_refresh_rejects_access_token_in_cookie(client: TestClient) -> None:
    _register(client)
    login = client.post(
        "/api/v1/auth/login",
        json={"email": VALID_REGISTER["email"], "password": VALID_REGISTER["password"]},
    )
    client.cookies.set("refresh_token", login.json()["accessToken"], path="/api/v1/auth")
    response = client.post("/api/v1/auth/refresh")
    assert response.status_code == 401


def test_logout_clears_refresh_cookie(client: TestClient) -> None:
    _register(client)
    client.post(
        "/api/v1/auth/login",
        json={"email": VALID_REGISTER["email"], "password": VALID_REGISTER["password"]},
    )
    assert client.cookies.get("refresh_token")

    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 204

    refresh = client.post("/api/v1/auth/refresh")  # cookie gone → 401
    assert refresh.status_code == 401


def test_refresh_rejects_garbage_token(client: TestClient) -> None:
    client.cookies.set("refresh_token", "not.a.jwt", path="/api/v1/auth")
    response = client.post("/api/v1/auth/refresh")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
