from fastapi.testclient import TestClient

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
