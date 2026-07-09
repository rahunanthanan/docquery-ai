"""Admin user-management API tests (§2, §4.2, §8)."""

from fastapi.testclient import TestClient

from tests.conftest import set_user_role
from tests.test_documents import _auth_headers


def _admin(client: TestClient, email: str = "admin@example.com") -> dict[str, str]:
    headers = _auth_headers(client, email)
    set_user_role(email, "admin")
    return headers


def _user_id(client: TestClient, admin: dict[str, str], email: str) -> str:
    body = client.get("/api/v1/admin/users?limit=100", headers=admin).json()
    matches = [u["id"] for u in body["items"] if u["email"] == email]
    assert matches, f"{email} not in user list"
    user_id: str = matches[0]
    return user_id


def test_admin_users_requires_admin_role(client: TestClient) -> None:
    reviewer = _auth_headers(client, "reviewer@example.com")
    set_user_role("reviewer@example.com", "reviewer")
    assert client.get("/api/v1/admin/users", headers=reviewer).status_code == 403
    assert client.get("/api/v1/admin/users").status_code == 401


def test_admin_lists_all_users(client: TestClient) -> None:
    _auth_headers(client, "someone@example.com")
    admin = _admin(client)
    body = client.get("/api/v1/admin/users", headers=admin).json()
    assert body["total"] == 2
    emails = {u["email"] for u in body["items"]}
    assert emails == {"someone@example.com", "admin@example.com"}


def test_role_change_takes_effect_and_is_audited(client: TestClient) -> None:
    target_headers = _auth_headers(client, "promotee@example.com")
    admin = _admin(client)
    target_id = _user_id(client, admin, "promotee@example.com")

    # before: no reviewer access
    assert client.get("/api/v1/review/queue", headers=target_headers).status_code == 403

    response = client.patch(
        f"/api/v1/admin/users/{target_id}", headers=admin, json={"role": "reviewer"}
    )
    assert response.status_code == 200
    assert response.json()["role"] == "reviewer"

    # §2: role read from DB per request — effective immediately, same token
    assert client.get("/api/v1/review/queue", headers=target_headers).status_code == 200

    audit = client.get(
        "/api/v1/audit?action=user.role_changed", headers=admin
    ).json()
    assert audit["total"] == 1
    event = audit["items"][0]
    assert event["metadata"] == {"old_role": "user", "new_role": "reviewer"}
    assert event["actorEmail"] == "admin@example.com"


def test_deactivation_blocks_login(client: TestClient) -> None:
    _auth_headers(client, "victim@example.com")
    admin = _admin(client)
    target_id = _user_id(client, admin, "victim@example.com")

    response = client.patch(
        f"/api/v1/admin/users/{target_id}", headers=admin, json={"isActive": False}
    )
    assert response.status_code == 200 and response.json()["isActive"] is False

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "victim@example.com", "password": "documents pass 1"},
    )
    assert login.status_code == 401
    assert login.json()["error"]["code"] == "ACCOUNT_DISABLED"


def test_admin_cannot_modify_self(client: TestClient) -> None:
    admin = _admin(client)
    self_id = _user_id(client, admin, "admin@example.com")
    response = client.patch(
        f"/api/v1/admin/users/{self_id}", headers=admin, json={"role": "user"}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "CANNOT_MODIFY_SELF"


def test_patch_unknown_user_is_404(client: TestClient) -> None:
    admin = _admin(client)
    response = client.patch(
        "/api/v1/admin/users/00000000-0000-0000-0000-000000000000",
        headers=admin,
        json={"role": "reviewer"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "USER_NOT_FOUND"


def test_patch_with_no_fields_is_422(client: TestClient) -> None:
    _auth_headers(client, "target@example.com")
    admin = _admin(client)
    target_id = _user_id(client, admin, "target@example.com")
    assert (
        client.patch(f"/api/v1/admin/users/{target_id}", headers=admin, json={}).status_code
        == 422
    )
