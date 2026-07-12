from fastapi.testclient import TestClient


def register_user(client: TestClient, login: str, password: str = "password123") -> dict:
    response = client.post("/api/auth/register", json={"login": login, "password": password})
    assert response.status_code == 201, response.text
    return response.json()


def login_user(client: TestClient, login: str, password: str = "password123") -> dict[str, str]:
    response = client.post("/api/auth/login", json={"login": login, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_board(client: TestClient, headers: dict[str, str], title: str = "Доска") -> dict:
    response = client.post(
        "/api/tables",
        json={"title": title, "description": "Тестовая доска"},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def add_role(
    client: TestClient,
    headers: dict[str, str],
    board_id: int,
    login: str,
    role: str,
) -> dict:
    response = client.post(
        f"/api/tables/{board_id}/roles",
        json={"login": login, "role": role},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_column(
    client: TestClient,
    headers: dict[str, str],
    board_id: int,
    title: str,
    position: int | None = None,
    is_done: bool = False,
) -> dict:
    payload: dict[str, bool | int | str] = {"title": title, "is_done": is_done}
    if position is not None:
        payload["position"] = position
    response = client.post(f"/api/tables/{board_id}/columns", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def create_card(
    client: TestClient,
    headers: dict[str, str],
    board_id: int,
    column_id: int,
    title: str,
    position: int | None = None,
    assignee_id: int | None = None,
    priority: str | None = None,
    deadline: str | None = None,
    label_ids: list[int] | None = None,
) -> dict:
    payload: dict[str, int | str | list[int] | None] = {
        "column_id": column_id,
        "title": title,
        "description": None,
    }
    if position is not None:
        payload["position"] = position
    if assignee_id is not None:
        payload["assignee_id"] = assignee_id
    if priority is not None:
        payload["priority"] = priority
    if deadline is not None:
        payload["deadline"] = deadline
    if label_ids is not None:
        payload["label_ids"] = label_ids
    response = client.post(f"/api/tables/{board_id}/cards", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def create_label(
    client: TestClient,
    headers: dict[str, str],
    board_id: int,
    title: str,
    color: str = "#2563EB",
) -> dict:
    response = client.post(
        f"/api/tables/{board_id}/labels",
        json={"title": title, "color": color},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()
