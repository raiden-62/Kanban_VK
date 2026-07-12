from fastapi.testclient import TestClient

from tests.helpers import (
    add_role,
    create_board,
    create_card,
    create_column,
    create_label,
    login_user,
    register_user,
)


def test_label_crud_and_permissions(client: TestClient) -> None:
    register_user(client, "owner")
    register_user(client, "viewer")

    owner_headers = login_user(client, "owner")
    viewer_headers = login_user(client, "viewer")

    board = create_board(client, owner_headers, "Метки")
    add_role(client, owner_headers, board["id"], "viewer", "viewer")

    blocked = client.post(
        f"/api/tables/{board['id']}/labels",
        json={"title": "bug", "color": "#DC2626"},
        headers=viewer_headers,
    )
    assert blocked.status_code == 403

    label = create_label(client, owner_headers, board["id"], "bug", "#DC2626")
    assert label["title"] == "bug"

    duplicate = client.post(
        f"/api/tables/{board['id']}/labels",
        json={"title": "bug", "color": "#111827"},
        headers=owner_headers,
    )
    assert duplicate.status_code == 409

    invalid_color = client.post(
        f"/api/tables/{board['id']}/labels",
        json={"title": "bad", "color": "red"},
        headers=owner_headers,
    )
    assert invalid_color.status_code == 422

    listed = client.get(f"/api/tables/{board['id']}/labels", headers=viewer_headers)
    assert listed.status_code == 200
    assert listed.json()[0]["title"] == "bug"

    updated = client.patch(
        f"/api/tables/{board['id']}/labels/{label['id']}",
        json={"title": "backend", "color": "#2563EB"},
        headers=owner_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "backend"

    deleted = client.delete(f"/api/tables/{board['id']}/labels/{label['id']}", headers=owner_headers)
    assert deleted.status_code == 204
    assert client.get(f"/api/tables/{board['id']}/labels", headers=owner_headers).json() == []


def test_card_priority_labels_filters_and_overdue_cards(client: TestClient) -> None:
    owner = register_user(client, "owner")
    editor = register_user(client, "editor")
    register_user(client, "viewer")

    owner_headers = login_user(client, "owner")
    editor_headers = login_user(client, "editor")
    viewer_headers = login_user(client, "viewer")

    board = create_board(client, owner_headers, "Фильтры")
    add_role(client, owner_headers, board["id"], "editor", "editor")
    add_role(client, owner_headers, board["id"], "viewer", "viewer")

    todo = create_column(client, owner_headers, board["id"], "Нужно сделать")
    done = create_column(client, owner_headers, board["id"], "Готово", is_done=True)
    bug = create_label(client, owner_headers, board["id"], "bug", "#DC2626")
    backend = create_label(client, owner_headers, board["id"], "backend", "#2563EB")

    critical = create_card(
        client,
        editor_headers,
        board["id"],
        todo["id"],
        "Исправить критический баг",
        assignee_id=editor["id"],
        priority="critical",
        deadline="2026-01-01",
        label_ids=[bug["id"], backend["id"]],
    )
    medium = create_card(
        client,
        editor_headers,
        board["id"],
        todo["id"],
        "Написать документацию",
        priority="medium",
        deadline="2026-01-01",
    )
    done_overdue = create_card(
        client,
        owner_headers,
        board["id"],
        done["id"],
        "Уже закрытая старая задача",
        priority="high",
        deadline="2026-01-01",
    )

    assert critical["priority"] == "critical"
    assert {label["title"] for label in critical["labels"]} == {"bug", "backend"}

    by_priority = client.get(
        f"/api/tables/{board['id']}/cards",
        params={"priority": "critical"},
        headers=viewer_headers,
    )
    assert by_priority.status_code == 200
    assert [card["id"] for card in by_priority.json()] == [critical["id"]]

    by_label = client.get(
        f"/api/tables/{board['id']}/cards",
        params={"label_id": bug["id"]},
        headers=viewer_headers,
    )
    assert by_label.status_code == 200
    assert [card["id"] for card in by_label.json()] == [critical["id"]]

    by_text = client.get(
        f"/api/tables/{board['id']}/cards",
        params={"q": "документацию"},
        headers=viewer_headers,
    )
    assert by_text.status_code == 200
    assert [card["id"] for card in by_text.json()] == [medium["id"]]

    overdue = client.get(f"/api/tables/{board['id']}/cards/overdue", headers=viewer_headers)
    assert overdue.status_code == 200
    assert {card["id"] for card in overdue.json()} == {critical["id"], medium["id"]}
    assert done_overdue["id"] not in {card["id"] for card in overdue.json()}

    overdue_query = client.get(
        f"/api/tables/{board['id']}/cards",
        params={"overdue": "true"},
        headers=viewer_headers,
    )
    assert overdue_query.status_code == 200
    assert {card["id"] for card in overdue_query.json()} == {critical["id"], medium["id"]}

    updated_labels = client.patch(
        f"/api/tables/{board['id']}/cards/{medium['id']}",
        json={"label_ids": [backend["id"]], "priority": "high"},
        headers=editor_headers,
    )
    assert updated_labels.status_code == 200
    assert updated_labels.json()["priority"] == "high"
    assert [label["id"] for label in updated_labels.json()["labels"]] == [backend["id"]]

    assert owner["login"] == "owner"

