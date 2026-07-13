from dataclasses import dataclass, field
from typing import Any


@dataclass
class AppState:
    token: str | None = None
    current_user: dict[str, Any] | None = None
    boards: list[dict[str, Any]] = field(default_factory=list)
    current_board_id: int | None = None
    kanban: dict[str, Any] | None = None
    selected_card_id: int | None = None
    filters: dict[str, Any] = field(default_factory=dict)

    @property
    def is_authenticated(self) -> bool:
        return self.token is not None

    @property
    def selected_card(self) -> dict[str, Any] | None:
        if self.kanban is None or self.selected_card_id is None:
            return None
        for card in self.kanban.get("cards", []):
            if card["id"] == self.selected_card_id:
                return card
        return None

    def clear_session(self) -> None:
        self.token = None
        self.current_user = None
        self.boards = []
        self.current_board_id = None
        self.kanban = None
        self.selected_card_id = None
        self.filters = {}

