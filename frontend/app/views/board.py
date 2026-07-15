from __future__ import annotations

from datetime import date
from typing import Any

import flet as ft

from frontend.app.api_client import ApiError
from frontend.app.components.common import ghost_button, primary_button, show_error, text_field
from frontend.app.components.kanban import column_control
from frontend.app.drag_drop import calculate_drop_position
from frontend.app.flet_compat import border_all, border_only, padding_symmetric
from frontend.app.theme import PALETTE, PRIORITY_LABELS


class BoardViewMixin:
    def load_kanban(self, board_id: int) -> None:
        try:
            self.state.current_board_id = board_id
            self.state.kanban = self.api.get_kanban(board_id)
            self.state.selected_card_id = None
            self.render_board()
        except ApiError as error:
            self.handle_api_error(error)

    def refresh_kanban(self) -> None:
        if self.state.current_board_id is None:
            return
        self.state.kanban = self.api.get_kanban(self.state.current_board_id)
        self.render_board()

    def current_board_role(self) -> str | None:
        if not self.state.kanban or not self.state.current_user:
            return None
        current_user_id = self.state.current_user.get("id")
        for member in self.state.kanban.get("members", []):
            if member.get("user", {}).get("id") == current_user_id:
                return member.get("role")
        return None

    def can_edit_current_board(self) -> bool:
        return self.current_board_role() in {"owner", "editor"}

    def can_manage_current_board(self) -> bool:
        return self.current_board_role() == "owner"

    def render_board(self) -> None:
        kanban = self.state.kanban or {}
        board = kanban.get("board", {})
        columns = kanban.get("columns", [])
        cards = kanban.get("cards", [])
        labels = kanban.get("labels", [])
        selected_card = self.state.selected_card
        can_edit = self.can_edit_current_board()
        can_manage = self.can_manage_current_board()
        overdue_cards = self.overdue_cards(cards, columns)
        visible_cards = self.apply_filters(cards, columns)

        column_controls = self.board_lanes(columns, visible_cards, can_edit)
        board_controls = [
            ft.Container(
                expand=True,
                padding=16,
                content=ft.Column(
                    expand=True,
                    spacing=12,
                    controls=[
                        self.overdue_banner(overdue_cards),
                        ft.Row(
                            spacing=0,
                            scroll=ft.ScrollMode.AUTO,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                            controls=column_controls,
                        ),
                    ],
                ),
            )
        ]
        if selected_card is not None:
            board_controls.append(self.card_panel(selected_card, labels, columns, can_edit))

        board_body = ft.Row(
            expand=True,
            spacing=0,
            controls=board_controls,
        )

        self.render(
            ft.Column(
                expand=True,
                spacing=0,
                controls=[
                    self.app_bar(
                        board.get("title", "Доска"),
                        ft.IconButton(icon=ft.Icons.ARROW_BACK, tooltip="К доскам", on_click=lambda _: self.load_boards()),
                        actions=[self.board_actions_menu(board)] if can_manage else None,
                    ),
                    ft.Container(
                        bgcolor=PALETTE.surface,
                        border=border_only(bottom=ft.BorderSide(1, PALETTE.border)),
                        padding=padding_symmetric(horizontal=16, vertical=8),
                        content=ft.Row(
                            controls=[
                                *(
                                    [
                                        primary_button(
                                            "Колонка",
                                            self.open_create_column_dialog,
                                            ft.Icons.VIEW_COLUMN,
                                        ),
                                    ]
                                    if can_edit
                                    else []
                                ),
                                ghost_button("Участники", self.open_members_dialog, ft.Icons.GROUP),
                                *(
                                    [ghost_button("Метки", self.open_labels_dialog, ft.Icons.LABEL)]
                                    if can_edit
                                    else []
                                ),
                                ghost_button("Фильтры", self.open_filters_dialog, ft.Icons.FILTER_ALT),
                            ]
                        ),
                    ),
                    board_body,
                ],
            )
        )

    def board_actions_menu(self, board: dict[str, Any]) -> ft.PopupMenuButton:
        return ft.PopupMenuButton(
            icon=ft.Icons.MORE_VERT,
            tooltip="Действия с доской",
            items=[
                ft.PopupMenuItem(
                    content="Редактировать доску",
                    icon=ft.Icons.EDIT,
                    on_click=lambda _, board=board: self.open_edit_board_dialog(board),
                ),
                ft.PopupMenuItem(
                    content="Удалить доску",
                    icon=ft.Icons.DELETE,
                    on_click=lambda _, board=board: self.open_delete_board_dialog(board),
                ),
            ],
        )

    def board_lanes(
        self,
        columns: list[dict[str, Any]],
        visible_cards: list[dict[str, Any]],
        can_edit: bool,
    ) -> list[ft.Control]:
        controls: list[ft.Control] = [self.column_separator()]
        for column in columns:
            controls.append(
                ft.Container(
                    padding=padding_symmetric(horizontal=8, vertical=0),
                    content=column_control(
                        column,
                        [card for card in visible_cards if card["column_id"] == column["id"]],
                        self.open_card,
                        self.open_create_card_dialog,
                        self.open_edit_column_dialog,
                        self.open_delete_column_dialog,
                        self.move_card_left,
                        self.move_card_right,
                        self.drop_card,
                        can_edit,
                    ),
                )
            )
            controls.append(self.column_separator())
        if not columns:
            controls.extend(
                [
                    self.empty_column_hint("Новая колонка"),
                    self.column_separator(),
                    self.empty_column_hint("В работе"),
                    self.column_separator(),
                    self.empty_column_hint("Готово"),
                    self.column_separator(),
                ]
            )
        return controls

    def column_separator(self) -> ft.Container:
        return ft.Container(
            width=1,
            height=620,
            bgcolor=PALETTE.border,
        )

    def empty_column_hint(self, title: str) -> ft.Container:
        return ft.Container(
            width=300,
            padding=padding_symmetric(horizontal=8, vertical=0),
            content=ft.Container(
                height=620,
                bgcolor=PALETTE.surface,
                border=border_all(1, PALETTE.border),
                border_radius=8,
                padding=16,
                content=ft.Text(title, color=PALETTE.text_muted),
            ),
        )

    def overdue_cards(self, cards: list[dict[str, Any]], columns: list[dict[str, Any]]) -> list[dict[str, Any]]:
        done_columns = {column["id"] for column in columns if column.get("is_done")}
        today = date.today().isoformat()
        return [
            card
            for card in cards
            if card.get("deadline") and card["deadline"] < today and card["column_id"] not in done_columns
        ]

    def apply_filters(self, cards: list[dict[str, Any]], columns: list[dict[str, Any]]) -> list[dict[str, Any]]:
        filters = self.state.filters
        if not filters:
            return cards

        result = cards
        if filters.get("q"):
            query = filters["q"].lower()
            result = [
                card
                for card in result
                if query in card.get("title", "").lower()
                or query in (card.get("description") or "").lower()
            ]
        if filters.get("priority"):
            result = [card for card in result if card.get("priority") == filters["priority"]]
        if filters.get("label_id"):
            label_id = filters["label_id"]
            result = [
                card
                for card in result
                if any(label["id"] == label_id for label in card.get("labels", []))
            ]
        if filters.get("overdue"):
            overdue_ids = {card["id"] for card in self.overdue_cards(result, columns)}
            result = [card for card in result if card["id"] in overdue_ids]
        return result

    def overdue_banner(self, overdue_cards: list[dict[str, Any]]) -> ft.Control:
        if not overdue_cards:
            return ft.Container(height=0)
        return ft.Container(
            bgcolor=PALETTE.overdue_bg,
            border=border_all(1, "#F4B4B4"),
            border_radius=6,
            padding=padding_symmetric(horizontal=12, vertical=10),
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.WARNING_AMBER, color=PALETTE.overdue_text),
                    ft.Text(f"Просрочено карточек: {len(overdue_cards)}", color=PALETTE.overdue_text, weight=ft.FontWeight.W_600),
                    ft.Text("Откройте фильтры, чтобы показать только просроченные задачи.", color=PALETTE.overdue_text),
                ]
            ),
        )

    def assignee_options(
        self,
        members: list[dict[str, Any]],
        query: str = "",
        selected_value: str | None = None,
    ) -> list[ft.dropdown.Option]:
        normalized_query = query.strip().lower()
        options = [ft.dropdown.Option("none", "Без исполнителя")]
        for member in members:
            user = member.get("user", {})
            user_id = user.get("id")
            login = user.get("login", "")
            if user_id is None:
                continue
            value = str(user_id)
            label = f"{login} (#{user_id})"
            matches_query = (
                not normalized_query
                or normalized_query in login.lower()
                or normalized_query in value
            )
            if matches_query or value == selected_value:
                options.append(ft.dropdown.Option(value, label))
        return options

    def card_panel(
        self,
        card: dict[str, Any] | None,
        labels: list[dict[str, Any]],
        columns: list[dict[str, Any]],
        can_edit: bool,
    ) -> ft.Container:
        if card is None:
            return ft.Container(width=0)

        title = text_field("Название")
        title.value = card["title"]
        title.read_only = not can_edit
        description = text_field("Описание", multiline=True)
        description.value = card.get("description") or ""
        description.read_only = not can_edit
        members = self.state.kanban.get("members", []) if self.state.kanban else []
        assignee_value = str(card["assignee_id"]) if card.get("assignee_id") else "none"
        assignee = ft.Dropdown(
            label="Исполнитель",
            value=assignee_value,
            options=self.assignee_options(members, selected_value=assignee_value),
            disabled=not can_edit,
        )
        assignee_status = (
            ft.Text("Пользователь удален", color=PALETTE.danger)
            if card.get("assignee_removed")
            else ft.Container(height=0)
        )
        deadline = text_field("Дедлайн YYYY-MM-DD")
        deadline.value = card.get("deadline") or ""
        deadline.read_only = not can_edit
        priority = ft.Dropdown(
            label="Приоритет",
            value=card.get("priority", "medium"),
            options=[ft.dropdown.Option(key, label) for key, label in PRIORITY_LABELS.items()],
            disabled=not can_edit,
        )
        selected_label_ids = {label["id"] for label in card.get("labels", [])}
        label_checks = [
            ft.Checkbox(
                label=label["title"],
                value=label["id"] in selected_label_ids,
                data=label["id"],
                disabled=not can_edit,
            )
            for label in labels
        ]

        def save(_: ft.ControlEvent) -> None:
            payload = {
                "title": title.value,
                "description": description.value or None,
                "assignee_id": int(assignee.value) if assignee.value != "none" else None,
                "deadline": deadline.value or None,
                "priority": priority.value,
                "label_ids": [checkbox.data for checkbox in label_checks if checkbox.value],
            }
            try:
                self.api.update_card(self.state.current_board_id, card["id"], payload)
                self.refresh_kanban()
            except (ApiError, ValueError) as error:
                show_error(self.page, str(error))

        def delete(_: ft.ControlEvent) -> None:
            try:
                self.api.delete_card(self.state.current_board_id, card["id"])
                self.state.selected_card_id = None
                self.refresh_kanban()
            except ApiError as error:
                self.handle_api_error(error)

        comments = self.load_comments_for_panel(card["id"])
        comment_field = text_field("Комментарий")

        def add_comment(_: ft.ControlEvent) -> None:
            if not comment_field.value:
                return
            try:
                self.api.create_comment(self.state.current_board_id, card["id"], comment_field.value)
                self.refresh_kanban()
            except ApiError as error:
                self.handle_api_error(error)

        action_controls: list[ft.Control] = []
        if can_edit:
            action_controls.append(
                ft.Row(
                    controls=[
                        primary_button("Сохранить", save, ft.Icons.SAVE),
                        ghost_button("Удалить", delete, ft.Icons.DELETE),
                    ]
                )
            )
        comment_controls: list[ft.Control] = []
        if can_edit:
            comment_controls.extend(
                [
                    comment_field,
                    primary_button("Добавить комментарий", add_comment, ft.Icons.ADD_COMMENT),
                ]
            )

        return ft.Container(
            width=390,
            bgcolor=PALETTE.surface,
            border=border_only(left=ft.BorderSide(1, PALETTE.border)),
            padding=16,
            content=ft.Column(
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                spacing=12,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text("Карточка", size=18, weight=ft.FontWeight.W_700),
                            ft.IconButton(icon=ft.Icons.CLOSE, tooltip="Закрыть", on_click=lambda _: self.close_card()),
                        ],
                    ),
                    title,
                    description,
                    assignee,
                    assignee_status,
                    deadline,
                    priority,
                    ft.Text("Метки", weight=ft.FontWeight.W_600),
                    ft.Column(spacing=2, controls=label_checks) if label_checks else ft.Text("Меток нет", color=PALETTE.text_muted),
                    *action_controls,
                    ft.Divider(),
                    ft.Text("Комментарии", weight=ft.FontWeight.W_600),
                    ft.Column(
                        spacing=6,
                        controls=[
                            ft.Container(
                                bgcolor=PALETTE.surface_muted,
                                border_radius=6,
                                padding=8,
                                content=ft.Text(comment["text"]),
                            )
                            for comment in comments
                        ],
                    ),
                    *comment_controls,
                ],
            ),
        )

    def load_comments_for_panel(self, card_id: int) -> list[dict[str, Any]]:
        try:
            return self.api.list_comments(self.state.current_board_id, card_id)
        except ApiError:
            return []

    def open_card(self, card_id: int) -> None:
        self.state.selected_card_id = card_id
        self.render_board()

    def close_card(self) -> None:
        self.state.selected_card_id = None
        self.render_board()

    def move_card_left(self, card: dict[str, Any]) -> None:
        self.move_card_by_delta(card, -1)

    def move_card_right(self, card: dict[str, Any]) -> None:
        self.move_card_by_delta(card, 1)

    def move_card_by_delta(self, card: dict[str, Any], delta: int) -> None:
        if not self.can_edit_current_board():
            return
        columns = self.state.kanban.get("columns", []) if self.state.kanban else []
        current_index = next((index for index, column in enumerate(columns) if column["id"] == card["column_id"]), None)
        if current_index is None:
            return
        target_index = current_index + delta
        if target_index < 0 or target_index >= len(columns):
            return
        try:
            self.api.move_card(self.state.current_board_id, card["id"], columns[target_index]["id"], 0)
            self.refresh_kanban()
        except ApiError as error:
            self.handle_api_error(error)

    def drop_card(
        self,
        dragged_card_id: int,
        target_column_id: int,
        after_card_id: int | None,
        empty_column_position: str = "top",
    ) -> None:
        if not self.can_edit_current_board() or self.state.kanban is None:
            return
        cards = self.state.kanban.get("cards", [])
        dragged_card = next((card for card in cards if card["id"] == dragged_card_id), None)
        if dragged_card is None:
            return
        target_cards = [card for card in cards if card["column_id"] == target_column_id]
        target_position = calculate_drop_position(
            target_cards,
            dragged_card_id,
            after_card_id,
            empty_column_position=empty_column_position,
        )
        try:
            self.api.move_card(self.state.current_board_id, dragged_card_id, target_column_id, target_position)
            self.refresh_kanban()
        except ApiError as error:
            self.handle_api_error(error)

