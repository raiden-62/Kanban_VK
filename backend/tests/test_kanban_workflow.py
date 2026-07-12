from fastapi.testclient import TestClient

from tests.helpers import add_role, create_board, create_card, create_column, login_user, register_user


def test_columns_cards_moves_assignment_deadline_and_comments(client: TestClient) -> None:
    register_user(client, "owner")
    editor = register_user(client, "editor")
    register_user(client, "viewer")
    stranger = register_user(client, "stranger")

    owner_headers = login_user(client, "owner")
    editor_headers = login_user(client, "editor")
    viewer_headers = login_user(client, "viewer")

    board = create_board(client, owner_headers, "Kanban")
    add_role(client, owner_headers, board["id"], "editor", "editor")
    add_role(client, owner_headers, board["id"], "viewer", "viewer")

    todo = create_column(client, editor_headers, board["id"], "Нужно сделать")
    done = create_column(client, editor_headers, board["id"], "Готово")
    progress = create_column(client, editor_headers, board["id"], "В работе", position=1)

    columns = client.get(f"/api/tables/{board['id']}/columns", headers=viewer_headers)
    assert columns.status_code == 200
    assert [column["title"] for column in columns.json()] == ["Нужно сделать", "В работе", "Готово"]
    assert [column["position"] for column in columns.json()] == [0, 1, 2]

    first = create_card(
        client,
        editor_headers,
        board["id"],
        todo["id"],
        "Первая карточка",
        assignee_id=editor["id"],
    )
    second = create_card(
        client,
        editor_headers,
        board["id"],
        todo["id"],
        "Вторая карточка",
        position=0,
    )

    todo_cards = client.get(
        f"/api/tables/{board['id']}/cards",
        params={"column_id": todo["id"]},
        headers=viewer_headers,
    )
    assert todo_cards.status_code == 200
    assert [card["title"] for card in todo_cards.json()] == ["Вторая карточка", "Первая карточка"]
    assert [card["position"] for card in todo_cards.json()] == [0, 1]

    updated = client.patch(
        f"/api/tables/{board['id']}/cards/{first['id']}",
        json={
            "title": "Первая карточка обновлена",
            "description": "Подробное описание",
            "assignee_id": editor["id"],
            "deadline": "2026-08-01",
        },
        headers=editor_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["description"] == "Подробное описание"
    assert updated.json()["deadline"] == "2026-08-01"

    invalid_assignee = client.patch(
        f"/api/tables/{board['id']}/cards/{first['id']}",
        json={"assignee_id": stranger["id"]},
        headers=editor_headers,
    )
    assert invalid_assignee.status_code == 400

    moved = client.patch(
        f"/api/tables/{board['id']}/cards/{first['id']}/move",
        json={"column_id": progress["id"], "position": 0},
        headers=editor_headers,
    )
    assert moved.status_code == 200
    assert moved.json()["column_id"] == progress["id"]
    assert moved.json()["position"] == 0

    remaining_todo_cards = client.get(
        f"/api/tables/{board['id']}/cards",
        params={"column_id": todo["id"]},
        headers=viewer_headers,
    )
    assert [card["id"] for card in remaining_todo_cards.json()] == [second["id"]]
    assert remaining_todo_cards.json()[0]["position"] == 0

    viewer_comment = client.post(
        f"/api/tables/{board['id']}/cards/{first['id']}/comments",
        json={"text": "Я только смотрю"},
        headers=viewer_headers,
    )
    assert viewer_comment.status_code == 403

    comment = client.post(
        f"/api/tables/{board['id']}/cards/{first['id']}/comments",
        json={"text": "Комментарий исполнителя"},
        headers=editor_headers,
    )
    assert comment.status_code == 201
    comment_id = comment.json()["id"]

    comments = client.get(
        f"/api/tables/{board['id']}/cards/{first['id']}/comments",
        headers=viewer_headers,
    )
    assert comments.status_code == 200
    assert comments.json()[0]["text"] == "Комментарий исполнителя"

    edited_comment = client.patch(
        f"/api/tables/{board['id']}/cards/{first['id']}/comments/{comment_id}",
        json={"text": "Комментарий обновлен"},
        headers=editor_headers,
    )
    assert edited_comment.status_code == 200
    assert edited_comment.json()["text"] == "Комментарий обновлен"

    deleted_comment = client.delete(
        f"/api/tables/{board['id']}/cards/{first['id']}/comments/{comment_id}",
        headers=owner_headers,
    )
    assert deleted_comment.status_code == 204

    deleted_column = client.delete(f"/api/tables/{board['id']}/columns/{done['id']}", headers=editor_headers)
    assert deleted_column.status_code == 204


def test_card_delete_normalizes_positions(client: TestClient) -> None:
    register_user(client, "owner")
    owner_headers = login_user(client, "owner")
    board = create_board(client, owner_headers, "Порядок")
    column = create_column(client, owner_headers, board["id"], "Очередь")

    first = create_card(client, owner_headers, board["id"], column["id"], "1")
    second = create_card(client, owner_headers, board["id"], column["id"], "2")
    third = create_card(client, owner_headers, board["id"], column["id"], "3")

    deleted = client.delete(f"/api/tables/{board['id']}/cards/{second['id']}", headers=owner_headers)
    assert deleted.status_code == 204

    cards = client.get(
        f"/api/tables/{board['id']}/cards",
        params={"column_id": column["id"]},
        headers=owner_headers,
    )
    assert cards.status_code == 200
    assert [card["id"] for card in cards.json()] == [first["id"], third["id"]]
    assert [card["position"] for card in cards.json()] == [0, 1]
