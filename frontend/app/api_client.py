from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class ApiError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class ApiClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000/api") -> None:
        self.base_url = base_url.rstrip("/")
        self.token: str | None = None

    def set_token(self, token: str | None) -> None:
        self.token = token

    def request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        query = ""
        if params:
            clean_params = {key: value for key, value in params.items() if value not in (None, "")}
            if clean_params:
                query = f"?{urlencode(clean_params)}"
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        req = Request(f"{self.base_url}{path}{query}", data=body, headers=headers, method=method)
        try:
            with urlopen(req, timeout=10) as response:
                data = response.read()
                if not data:
                    return None
                return json.loads(data.decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8")
            try:
                parsed = json.loads(detail)
                message = parsed.get("detail", detail)
            except json.JSONDecodeError:
                message = detail
            raise ApiError(str(message), exc.code) from exc
        except URLError as exc:
            raise ApiError("Backend недоступен. Проверьте, что API запущен.") from exc

    def register(self, login: str, password: str) -> dict[str, Any]:
        return self.request("POST", "/auth/register", {"login": login, "password": password})

    def login(self, login: str, password: str) -> str:
        response = self.request("POST", "/auth/login", {"login": login, "password": password})
        token = response["access_token"]
        self.set_token(token)
        return token

    def me(self) -> dict[str, Any]:
        return self.request("GET", "/auth/me")

    def list_boards(self) -> list[dict[str, Any]]:
        return self.request("GET", "/tables")

    def create_board(self, title: str, description: str | None = None) -> dict[str, Any]:
        return self.request("POST", "/tables", {"title": title, "description": description})

    def update_board(self, board_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("PATCH", f"/tables/{board_id}", payload)

    def delete_board(self, board_id: int) -> None:
        self.request("DELETE", f"/tables/{board_id}")

    def get_kanban(self, board_id: int) -> dict[str, Any]:
        return self.request("GET", f"/tables/{board_id}/kanban")

    def get_overdue_cards(self, board_id: int) -> list[dict[str, Any]]:
        return self.request("GET", f"/tables/{board_id}/cards/overdue")

    def create_column(self, board_id: int, title: str, is_done: bool = False) -> dict[str, Any]:
        return self.request("POST", f"/tables/{board_id}/columns", {"title": title, "is_done": is_done})

    def update_column(self, board_id: int, column_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("PATCH", f"/tables/{board_id}/columns/{column_id}", payload)

    def delete_column(self, board_id: int, column_id: int) -> None:
        self.request("DELETE", f"/tables/{board_id}/columns/{column_id}")

    def create_card(self, board_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", f"/tables/{board_id}/cards", payload)

    def update_card(self, board_id: int, card_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("PATCH", f"/tables/{board_id}/cards/{card_id}", payload)

    def delete_card(self, board_id: int, card_id: int) -> None:
        self.request("DELETE", f"/tables/{board_id}/cards/{card_id}")

    def move_card(self, board_id: int, card_id: int, column_id: int, position: int) -> dict[str, Any]:
        return self.request("PATCH", f"/tables/{board_id}/cards/{card_id}/move", {"column_id": column_id, "position": position})

    def list_comments(self, board_id: int, card_id: int) -> list[dict[str, Any]]:
        return self.request("GET", f"/tables/{board_id}/cards/{card_id}/comments")

    def create_comment(self, board_id: int, card_id: int, text: str) -> dict[str, Any]:
        return self.request("POST", f"/tables/{board_id}/cards/{card_id}/comments", {"text": text})

    def list_roles(self, board_id: int) -> list[dict[str, Any]]:
        return self.request("GET", f"/tables/{board_id}/roles")

    def add_role(self, board_id: int, login: str, role: str) -> dict[str, Any]:
        return self.request("POST", f"/tables/{board_id}/roles", {"login": login, "role": role})

    def update_role(self, board_id: int, user_id: int, role: str) -> dict[str, Any]:
        return self.request("PATCH", f"/tables/{board_id}/roles/{user_id}", {"role": role})

    def delete_role(self, board_id: int, user_id: int) -> None:
        self.request("DELETE", f"/tables/{board_id}/roles/{user_id}")

    def list_labels(self, board_id: int) -> list[dict[str, Any]]:
        return self.request("GET", f"/tables/{board_id}/labels")

    def create_label(self, board_id: int, title: str, color: str) -> dict[str, Any]:
        return self.request("POST", f"/tables/{board_id}/labels", {"title": title, "color": color})

    def search_users(self, query: str) -> list[dict[str, Any]]:
        return self.request("GET", "/users", params={"q": query})
