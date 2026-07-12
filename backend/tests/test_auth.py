from fastapi.testclient import TestClient

from app.core.security import get_password_hash, verify_password
from tests.helpers import login_user, register_user


def test_register_login_and_me(client: TestClient) -> None:
    unauthorized = client.get("/api/tables")
    assert unauthorized.status_code == 401

    user = register_user(client, "alice")
    assert user["login"] == "alice"
    assert "password" not in user
    assert "password_hash" not in user

    duplicate = client.post(
        "/api/auth/register",
        json={"login": "alice", "password": "password123"},
    )
    assert duplicate.status_code == 409

    bad_login = client.post(
        "/api/auth/login",
        json={"login": "alice", "password": "wrong-password"},
    )
    assert bad_login.status_code == 401

    headers = login_user(client, "alice")
    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["login"] == "alice"


def test_invalid_token_is_rejected(client: TestClient) -> None:
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer broken-token"})
    assert response.status_code == 401


def test_password_hash_is_not_plain_text_and_verifies() -> None:
    password_hash = get_password_hash("password123")
    assert password_hash != "password123"
    assert verify_password("password123", password_hash)
    assert not verify_password("wrong-password", password_hash)


def test_user_search_requires_auth_and_filters_by_login(client: TestClient) -> None:
    register_user(client, "alice")
    register_user(client, "alex")
    register_user(client, "boris")

    assert client.get("/api/users", params={"q": "al"}).status_code == 401

    headers = login_user(client, "alice")
    response = client.get("/api/users", params={"q": "al"}, headers=headers)
    assert response.status_code == 200
    assert [user["login"] for user in response.json()] == ["alex", "alice"]
