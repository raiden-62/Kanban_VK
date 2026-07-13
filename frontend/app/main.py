from __future__ import annotations

from datetime import date
from typing import Any

import flet as ft

from frontend.app.api_client import ApiClient, ApiError
from frontend.app.components.common import ghost_button, primary_button, show_error, show_info, text_field
from frontend.app.components.kanban import column_control, label_chip, priority_chip
from frontend.app.flet_compat import border_all, border_only, padding_symmetric
from frontend.app.state import AppState
from frontend.app.theme import PALETTE, PRIORITY_LABELS, ROLE_LABELS


class KanbanFrontend:
    TEST_LOGIN = "testuser"
    TEST_PASSWORD = "123123123"

    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.api = ApiClient()
        self.state = AppState()

        self.page.title = "VK Kanban"
        self.page.bgcolor = PALETTE.app_bg
        self.page.padding = 0
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.window_min_width = 1100
        self.page.window_min_height = 720

    def run(self) -> None:
        self.render_auth()

    def render(self, control: ft.Control) -> None:
        self.page.controls.clear()
        self.page.add(control)
        self.page.update()

    def handle_api_error(self, error: ApiError) -> None:
        show_error(self.page, str(error))

    def complete_login(self, token: str) -> None:
        self.state.token = token
        self.state.current_user = self.api.me()
        self.load_boards()

    def render_auth(self) -> None:
        login_field = text_field("Логин")
        password_field = text_field("Пароль", password=True)
        auth_mode = {"value": "login"}

        def change_mode(event: ft.ControlEvent) -> None:
            selected = event.control.selected or []
            auth_mode["value"] = selected[0] if selected else "login"

        mode = ft.SegmentedButton(
            selected=["login"],
            on_change=change_mode,
            segments=[
                ft.Segment(value="login", label=ft.Text("Вход"), icon=ft.Icon(ft.Icons.LOGIN)),
                ft.Segment(value="register", label=ft.Text("Регистрация"), icon=ft.Icon(ft.Icons.PERSON_ADD)),
            ],
        )

        def submit(_: ft.ControlEvent) -> None:
            login = login_field.value.strip() if login_field.value else ""
            password = password_field.value or ""
            if not login or not password:
                show_error(self.page, "Введите логин и пароль")
                return
            try:
                if auth_mode["value"] == "register":
                    self.api.register(login, password)
                token = self.api.login(login, password)
                self.complete_login(token)
            except ApiError as error:
                self.handle_api_error(error)

        def test_login(_: ft.ControlEvent) -> None:
            try:
                token = self.api.login(self.TEST_LOGIN, self.TEST_PASSWORD)
            except ApiError as login_error:
                if login_error.status_code != 401:
                    self.handle_api_error(login_error)
                    return
                try:
                    self.api.register(self.TEST_LOGIN, self.TEST_PASSWORD)
                    token = self.api.login(self.TEST_LOGIN, self.TEST_PASSWORD)
                except ApiError as register_error:
                    self.handle_api_error(register_error)
                    return
            self.complete_login(token)

        self.render(
            ft.Container(
                expand=True,
                alignment=ft.Alignment(0, 0),
                content=ft.Container(
                    width=420,
                    bgcolor=PALETTE.surface,
                    border=border_all(1, PALETTE.border),
                    border_radius=8,
                    padding=24,
                    content=ft.Column(
                        spacing=18,
                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                        controls=[
                            ft.Text("VK Kanban", size=28, weight=ft.FontWeight.W_700, color=PALETTE.text),
                            mode,
                            login_field,
                            password_field,
                            primary_button("Продолжить", submit, ft.Icons.ARROW_FORWARD),
                            ghost_button("Тестовый вход", test_login, ft.Icons.BOLT),
                        ],
                    ),
                ),
            )
        )

    def load_boards(self) -> None:
        try:
            self.state.boards = self.api.list_boards()
            self.render_boards()
        except ApiError as error:
            self.handle_api_error(error)

    def app_bar(self, title: str, leading: ft.Control | None = None) -> ft.Container:
        controls: list[ft.Control] = []
        if leading is not None:
            controls.append(leading)
        controls.extend(
            [
                ft.Text(title, size=20, weight=ft.FontWeight.W_700, color=PALETTE.text, expand=True),
                ft.Text(self.state.current_user["login"] if self.state.current_user else "", color=PALETTE.text_muted),
                ft.IconButton(icon=ft.Icons.LOGOUT, tooltip="Выйти", on_click=lambda _: self.logout()),
            ]
        )
        return ft.Container(
            bgcolor=PALETTE.surface,
            border=border_only(bottom=ft.BorderSide(1, PALETTE.border)),
            padding=padding_symmetric(horizontal=20, vertical=12),
            content=ft.Row(controls=controls, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        )

    def logout(self) -> None:
        self.api.set_token(None)
        self.state.clear_session()
        self.render_auth()

    def render_boards(self) -> None:
        def open_create_dialog(_: ft.ControlEvent) -> None:
            title = text_field("Название")
            description = text_field("Описание", multiline=True)

            def create(_: ft.ControlEvent) -> None:
                if not title.value:
                    show_error(self.page, "Введите название доски")
                    return
                try:
                    self.api.create_board(title.value, description.value or None)
                    dialog.open = False
                    self.load_boards()
                except ApiError as error:
                    self.handle_api_error(error)

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Новая доска"),
                content=ft.Column(width=420, tight=True, controls=[title, description]),
                actions=[ghost_button("Отмена", lambda _: self.close_dialog(dialog)), primary_button("Создать", create)],
            )
            self.open_dialog(dialog)

        board_cards = []
        for board in self.state.boards:
            board_cards.append(
                ft.Container(
                    bgcolor=PALETTE.surface,
                    border=border_all(1, PALETTE.border),
                    border_radius=8,
                    padding=16,
                    width=320,
                    on_click=lambda _, board_id=board["id"]: self.load_kanban(board_id),
                    content=ft.Column(
                        spacing=8,
                        controls=[
                            ft.Text(board["title"], size=17, weight=ft.FontWeight.W_600),
                            ft.Text(board.get("description") or "Без описания", color=PALETTE.text_muted, max_lines=2),
                        ],
                    ),
                )
            )

        self.render(
            ft.Column(
                expand=True,
                spacing=0,
                controls=[
                    self.app_bar("Мои доски"),
                    ft.Container(
                        expand=True,
                        padding=20,
                        content=ft.Column(
                            spacing=18,
                            controls=[
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls=[
                                        ft.Text("Доступные доски", size=18, weight=ft.FontWeight.W_600),
                                        primary_button("Создать доску", open_create_dialog, ft.Icons.ADD),
                                    ],
                                ),
                                ft.Row(wrap=True, spacing=12, run_spacing=12, controls=board_cards)
                                if board_cards
                                else ft.Text("Пока нет досок", color=PALETTE.text_muted),
                            ],
                        ),
                    ),
                ],
            )
        )

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

    def render_board(self) -> None:
        kanban = self.state.kanban or {}
        board = kanban.get("board", {})
        columns = kanban.get("columns", [])
        cards = kanban.get("cards", [])
        labels = kanban.get("labels", [])
        selected_card = self.state.selected_card
        overdue_cards = self.overdue_cards(cards, columns)
        visible_cards = self.apply_filters(cards, columns)

        column_controls = self.board_lanes(columns, visible_cards)
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
            board_controls.append(self.card_panel(selected_card, labels, columns))

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
                    ),
                    ft.Container(
                        bgcolor=PALETTE.surface,
                        border=border_only(bottom=ft.BorderSide(1, PALETTE.border)),
                        padding=padding_symmetric(horizontal=16, vertical=8),
                        content=ft.Row(
                            controls=[
                                primary_button("Колонка", self.open_create_column_dialog, ft.Icons.VIEW_COLUMN),
                                ghost_button("Участники", self.open_members_dialog, ft.Icons.GROUP),
                                ghost_button("Метки", self.open_labels_dialog, ft.Icons.LABEL),
                                ghost_button("Фильтры", self.open_filters_dialog, ft.Icons.FILTER_ALT),
                            ]
                        ),
                    ),
                    board_body,
                ],
            )
        )

    def board_lanes(self, columns: list[dict[str, Any]], visible_cards: list[dict[str, Any]]) -> list[ft.Control]:
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

    def card_panel(self, card: dict[str, Any] | None, labels: list[dict[str, Any]], columns: list[dict[str, Any]]) -> ft.Container:
        if card is None:
            return ft.Container(width=0)

        title = text_field("Название")
        title.value = card["title"]
        description = text_field("Описание", multiline=True)
        description.value = card.get("description") or ""
        assignee = text_field("ID исполнителя")
        assignee.value = str(card.get("assignee_id") or "")
        deadline = text_field("Дедлайн YYYY-MM-DD")
        deadline.value = card.get("deadline") or ""
        priority = ft.Dropdown(
            label="Приоритет",
            value=card.get("priority", "medium"),
            options=[ft.dropdown.Option(key, label) for key, label in PRIORITY_LABELS.items()],
        )
        selected_label_ids = {label["id"] for label in card.get("labels", [])}
        label_checks = [
            ft.Checkbox(label=label["title"], value=label["id"] in selected_label_ids, data=label["id"])
            for label in labels
        ]

        def save(_: ft.ControlEvent) -> None:
            payload = {
                "title": title.value,
                "description": description.value or None,
                "assignee_id": int(assignee.value) if assignee.value else None,
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
                    deadline,
                    priority,
                    ft.Text("Метки", weight=ft.FontWeight.W_600),
                    ft.Column(spacing=2, controls=label_checks) if label_checks else ft.Text("Меток нет", color=PALETTE.text_muted),
                    ft.Row(controls=[primary_button("Сохранить", save, ft.Icons.SAVE), ghost_button("Удалить", delete, ft.Icons.DELETE)]),
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
                    comment_field,
                    primary_button("Добавить комментарий", add_comment, ft.Icons.ADD_COMMENT),
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

    def open_create_column_dialog(self, _: ft.ControlEvent) -> None:
        title = text_field("Название колонки")
        is_done = ft.Checkbox(label="Завершающая колонка", value=False)

        def create(_: ft.ControlEvent) -> None:
            if not title.value:
                show_error(self.page, "Введите название колонки")
                return
            try:
                self.api.create_column(self.state.current_board_id, title.value, bool(is_done.value))
                self.close_dialog(dialog)
                self.refresh_kanban()
            except ApiError as error:
                self.handle_api_error(error)

        title.on_submit = create
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Новая колонка"),
            content=ft.Column(width=420, tight=True, controls=[title, is_done]),
            actions=[ghost_button("Отмена", lambda _: self.close_dialog(dialog)), primary_button("Создать", create)],
        )
        self.open_dialog(dialog)

    def open_edit_column_dialog(self, column: dict[str, Any]) -> None:
        title = text_field("Название колонки")
        title.value = column["title"]
        is_done = ft.Checkbox(label="Завершающая колонка", value=bool(column.get("is_done")))

        def save(_: ft.ControlEvent) -> None:
            if not title.value:
                show_error(self.page, "Введите название колонки")
                return
            try:
                self.api.update_column(
                    self.state.current_board_id,
                    column["id"],
                    {"title": title.value, "is_done": bool(is_done.value)},
                )
                self.close_dialog(dialog)
                self.refresh_kanban()
            except ApiError as error:
                self.handle_api_error(error)

        title.on_submit = save
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Редактировать колонку"),
            content=ft.Column(width=420, tight=True, controls=[title, is_done]),
            actions=[ghost_button("Отмена", lambda _: self.close_dialog(dialog)), primary_button("Сохранить", save)],
        )
        self.open_dialog(dialog)

    def open_delete_column_dialog(self, column: dict[str, Any]) -> None:
        def delete(_: ft.ControlEvent) -> None:
            try:
                self.api.delete_column(self.state.current_board_id, column["id"])
                self.close_dialog(dialog)
                self.refresh_kanban()
            except ApiError as error:
                self.handle_api_error(error)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Удалить колонку"),
            content=ft.Text(f"Колонка «{column['title']}» и все ее карточки будут удалены."),
            actions=[
                ghost_button("Отмена", lambda _: self.close_dialog(dialog)),
                primary_button("Удалить", delete, ft.Icons.DELETE),
            ],
        )
        self.open_dialog(dialog)

    def open_create_card_dialog(self, column_id: int) -> None:
        title = text_field("Название")
        description = text_field("Описание", multiline=True)

        def create(_: ft.ControlEvent) -> None:
            if not title.value:
                show_error(self.page, "Введите название карточки")
                return
            try:
                card = self.api.create_card(
                    self.state.current_board_id,
                    {"column_id": column_id, "title": title.value, "description": description.value or None},
                )
                self.state.selected_card_id = card["id"]
                self.close_dialog(dialog)
                self.refresh_kanban()
            except ApiError as error:
                self.handle_api_error(error)

        title.on_submit = create
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Новая карточка"),
            content=ft.Column(width=420, tight=True, controls=[title, description]),
            actions=[ghost_button("Отмена", lambda _: self.close_dialog(dialog)), primary_button("Создать", create)],
        )
        self.open_dialog(dialog)

    def open_members_dialog(self, _: ft.ControlEvent) -> None:
        login = text_field("Логин пользователя")
        role = ft.Dropdown(
            label="Роль",
            value="viewer",
            options=[
                ft.dropdown.Option("editor", ROLE_LABELS["editor"]),
                ft.dropdown.Option("viewer", ROLE_LABELS["viewer"]),
            ],
        )

        def add_member(_: ft.ControlEvent) -> None:
            if not login.value:
                show_error(self.page, "Введите логин")
                return
            try:
                self.api.add_role(self.state.current_board_id, login.value, role.value)
                self.close_dialog(dialog)
                self.refresh_kanban()
            except ApiError as error:
                self.handle_api_error(error)

        members = self.state.kanban.get("members", []) if self.state.kanban else []
        rows = [
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(member["user"]["login"]),
                    ft.Text(ROLE_LABELS.get(member["role"], member["role"]), color=PALETTE.text_muted),
                ],
            )
            for member in members
        ]
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Участники"),
            content=ft.Column(width=480, tight=True, controls=[*rows, ft.Divider(), login, role]),
            actions=[ghost_button("Закрыть", lambda _: self.close_dialog(dialog)), primary_button("Добавить", add_member)],
        )
        self.open_dialog(dialog)

    def open_labels_dialog(self, _: ft.ControlEvent) -> None:
        title = text_field("Название метки")
        color = text_field("Цвет #RRGGBB")
        color.value = "#2787F5"

        def create(_: ft.ControlEvent) -> None:
            if not title.value or not color.value:
                show_error(self.page, "Введите название и цвет")
                return
            try:
                self.api.create_label(self.state.current_board_id, title.value, color.value)
                self.close_dialog(dialog)
                self.refresh_kanban()
            except ApiError as error:
                self.handle_api_error(error)

        labels = self.state.kanban.get("labels", []) if self.state.kanban else []
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Метки"),
            content=ft.Column(
                width=420,
                tight=True,
                controls=[
                    ft.Row(wrap=True, spacing=6, controls=[label_chip(label) for label in labels]),
                    ft.Divider(),
                    title,
                    color,
                ],
            ),
            actions=[ghost_button("Закрыть", lambda _: self.close_dialog(dialog)), primary_button("Создать", create)],
        )
        self.open_dialog(dialog)

    def open_filters_dialog(self, _: ft.ControlEvent) -> None:
        filters = self.state.filters
        labels = self.state.kanban.get("labels", []) if self.state.kanban else []
        query = text_field("Поиск")
        query.value = filters.get("q", "")
        priority = ft.Dropdown(
            label="Приоритет",
            value=filters.get("priority") or "",
            options=[ft.dropdown.Option("", "Любой")]
            + [ft.dropdown.Option(key, label) for key, label in PRIORITY_LABELS.items()],
        )
        label = ft.Dropdown(
            label="Метка",
            value=str(filters.get("label_id") or ""),
            options=[ft.dropdown.Option("", "Любая")]
            + [ft.dropdown.Option(str(item["id"]), item["title"]) for item in labels],
        )
        overdue = ft.Checkbox(label="Только просроченные", value=bool(filters.get("overdue")))

        def apply(_: ft.ControlEvent) -> None:
            self.state.filters = {
                "q": query.value or "",
                "priority": priority.value or "",
                "label_id": int(label.value) if label.value else None,
                "overdue": bool(overdue.value),
            }
            self.close_dialog(dialog)
            self.render_board()

        def reset(_: ft.ControlEvent) -> None:
            self.state.filters = {}
            self.close_dialog(dialog)
            self.render_board()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Фильтры"),
            content=ft.Column(width=420, tight=True, controls=[query, priority, label, overdue]),
            actions=[
                ghost_button("Сбросить", reset, ft.Icons.CLEAR),
                primary_button("Применить", apply, ft.Icons.FILTER_ALT),
            ],
        )
        self.open_dialog(dialog)

    def open_dialog(self, dialog: ft.AlertDialog) -> None:
        self.page.show_dialog(dialog)

    def close_dialog(self, dialog: ft.AlertDialog) -> None:
        dialog.open = False
        self.page.pop_dialog()


def main(page: ft.Page) -> None:
    KanbanFrontend(page).run()


if __name__ == "__main__":
    ft.run(main)
