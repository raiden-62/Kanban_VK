from fastapi.testclient import TestClient

from tests.helpers import add_role, create_board, create_card, create_column, login_user, register_user


def test_board_crud_and_owner_membership(client: TestClient) -> None:
    owner = register_user(client, "owner")
    owner_headers = login_user(client, "owner")

    board = create_board(client, owner_headers, "Проект")
    assert board["owner_id"] == owner["id"]
    assert board["title"] == "Проект"

    board_list = client.get("/api/tables", headers=owner_headers)
    assert board_list.status_code == 200
    assert [item["id"] for item in board_list.json()] == [board["id"]]

    roles = client.get(f"/api/tables/{board['id']}/roles", headers=owner_headers)
    assert roles.status_code == 200
    assert roles.json()[0]["role"] == "owner"
    assert roles.json()[0]["user"]["login"] == "owner"

    updated = client.patch(
        f"/api/tables/{board['id']}",
        json={"title": "Обновленный проект", "description": "Описание"},
        headers=owner_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Обновленный проект"

    deleted = client.delete(f"/api/tables/{board['id']}", headers=owner_headers)
    assert deleted.status_code == 204
    assert client.get(f"/api/tables/{board['id']}", headers=owner_headers).status_code == 404


def test_board_role_permissions(client: TestClient) -> None:
    owner = register_user(client, "owner")
    editor = register_user(client, "editor")
    viewer = register_user(client, "viewer")
    register_user(client, "stranger")

    owner_headers = login_user(client, "owner")
    editor_headers = login_user(client, "editor")
    viewer_headers = login_user(client, "viewer")
    stranger_headers = login_user(client, "stranger")

    board = create_board(client, owner_headers, "Роли")
    add_role(client, owner_headers, board["id"], "editor", "editor")
    add_role(client, owner_headers, board["id"], "viewer", "viewer")

    assert client.get(f"/api/tables/{board['id']}", headers=viewer_headers).status_code == 200
    assert client.get(f"/api/tables/{board['id']}", headers=stranger_headers).status_code == 403

    viewer_create_column = client.post(
        f"/api/tables/{board['id']}/columns",
        json={"title": "Запрещено"},
        headers=viewer_headers,
    )
    assert viewer_create_column.status_code == 403

    editor_role_change = client.post(
        f"/api/tables/{board['id']}/roles",
        json={"login": "stranger", "role": "viewer"},
        headers=editor_headers,
    )
    assert editor_role_change.status_code == 403

    owner_role_duplicate = client.post(
        f"/api/tables/{board['id']}/roles",
        json={"login": "stranger", "role": "owner"},
        headers=owner_headers,
    )
    assert owner_role_duplicate.status_code == 400

    owner_remove = client.delete(
        f"/api/tables/{board['id']}/roles/{owner['id']}",
        headers=owner_headers,
    )
    assert owner_remove.status_code == 400

    role_update = client.patch(
        f"/api/tables/{board['id']}/roles/{viewer['id']}",
        json={"role": "editor"},
        headers=owner_headers,
    )
    assert role_update.status_code == 200
    assert role_update.json()["role"] == "editor"

    created_by_promoted_user = create_column(client, viewer_headers, board["id"], "После повышения")
    assert created_by_promoted_user["title"] == "После повышения"
    assigned_card = create_card(
        client,
        owner_headers,
        board["id"],
        created_by_promoted_user["id"],
        "Назначена удаляемому участнику",
        assignee_id=viewer["id"],
    )
    assert assigned_card["assignee_id"] == viewer["id"]
    assert assigned_card["assignee_removed"] is False

    role_delete = client.delete(f"/api/tables/{board['id']}/roles/{viewer['id']}", headers=owner_headers)
    assert role_delete.status_code == 204
    assert client.get(f"/api/tables/{board['id']}", headers=viewer_headers).status_code == 403
    unassigned_card = client.get(
        f"/api/tables/{board['id']}/cards/{assigned_card['id']}",
        headers=owner_headers,
    )
    assert unassigned_card.status_code == 200
    assert unassigned_card.json()["assignee_id"] is None
    assert unassigned_card.json()["assignee_removed"] is True

    # Keep the variable used so a future refactor does not remove the editor scenario accidentally.
    assert editor["login"] == "editor"
