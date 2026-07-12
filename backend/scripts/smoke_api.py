from __future__ import annotations

import argparse
import json
import time
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def request(
    base_url: str,
    method: str,
    path: str,
    token: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any] | list[Any] | None:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(f"{base_url}{path}", data=body, headers=headers, method=method)
    try:
        with urlopen(req, timeout=10) as response:
            content = response.read()
            if not content:
                return None
            return json.loads(content.decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8")
        raise RuntimeError(f"{method} {path} failed: {exc.code} {detail}") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a simple smoke scenario against a live Kanban API.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    suffix = int(time.time())
    login = f"smoke_{suffix}"
    password = "password123"

    request(args.base_url, "POST", "/api/auth/register", payload={"login": login, "password": password})
    token_response = request(args.base_url, "POST", "/api/auth/login", payload={"login": login, "password": password})
    token = token_response["access_token"]

    board = request(args.base_url, "POST", "/api/tables", token, {"title": "Smoke board", "description": None})
    todo = request(args.base_url, "POST", f"/api/tables/{board['id']}/columns", token, {"title": "Todo"})
    done = request(
        args.base_url,
        "POST",
        f"/api/tables/{board['id']}/columns",
        token,
        {"title": "Done", "is_done": True},
    )
    label = request(args.base_url, "POST", f"/api/tables/{board['id']}/labels", token, {"title": "smoke", "color": "#2563EB"})
    card = request(
        args.base_url,
        "POST",
        f"/api/tables/{board['id']}/cards",
        token,
        {
            "column_id": todo["id"],
            "title": "Smoke card",
            "description": "Created by smoke_api.py",
            "priority": "high",
            "label_ids": [label["id"]],
        },
    )
    request(args.base_url, "PATCH", f"/api/tables/{board['id']}/cards/{card['id']}/move", token, {"column_id": done["id"], "position": 0})
    request(args.base_url, "POST", f"/api/tables/{board['id']}/cards/{card['id']}/comments", token, {"text": "Smoke comment"})
    kanban = request(args.base_url, "GET", f"/api/tables/{board['id']}/kanban", token)

    print(json.dumps({"status": "ok", "board_id": board["id"], "cards": len(kanban["cards"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
