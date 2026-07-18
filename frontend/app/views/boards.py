from __future__ import annotations

from typing import Any

import flet as ft

from frontend.app.api_client import ApiError
from frontend.app.components.common import ghost_button, primary_button, show_error, text_field
from frontend.app.flet_compat import border_all, sync_control_value
from frontend.app.theme import PALETTE


BOARD_PRESETS: dict[str, dict[str, Any]] = {
    "empty": {
        "title": "Пустая",
        "columns": [],
    },
    "features": {
        "title": "Фичи",
        "columns": [
            {"title": "Не начато", "is_done": False},
            {"title": "В работе", "is_done": False},
            {"title": "На тестировании", "is_done": False},
            {"title": "Готово", "is_done": True},
        ],
    },
    "job_applications": {
        "title": "Отклики на вакансии",
        "columns": [
            {"title": "Резюме не рассмотрено", "is_done": False},
            {"title": "HR-интервью", "is_done": False},
            {"title": "Техническое интервью", "is_done": False},
            {"title": "Принят", "is_done": True},
        ],
    },
}


class BoardsViewMixin:
    def load_boards(self) -> None:
        try:
            self.state.current_board_id = None
            self.state.kanban = None
            self.state.selected_card_id = None
            self.state.filters = {}
            self.card_panel_scroll_offset = 0.0
            self.card_panel_has_unsaved_changes = False
            self.state.boards = self.api.list_boards()
            self.render_boards()
        except ApiError as error:
            self.handle_api_error(error)

    def is_board_owner(self, board: dict[str, Any]) -> bool:
        return bool(self.state.current_user and board.get("owner_id") == self.state.current_user.get("id"))

    def render_boards(self) -> None:
        def open_create_dialog(_: ft.ControlEvent) -> None:
            title = text_field("Название")
            description = text_field("Описание", multiline=True)
            preset = ft.Dropdown(
                label="Шаблон",
                value="empty",
                options=[
                    ft.dropdown.Option(key, item["title"])
                    for key, item in BOARD_PRESETS.items()
                ],
            )
            preset.on_select = sync_control_value

            def create(_: ft.ControlEvent) -> None:
                if not title.value:
                    show_error(self.page, "Введите название доски")
                    return
                try:
                    board = self.api.create_board(title.value, description.value or None)
                    for column in BOARD_PRESETS[preset.value]["columns"]:
                        self.api.create_column(board["id"], column["title"], column["is_done"])
                    dialog.open = False
                    self.load_boards()
                except ApiError as error:
                    self.handle_api_error(error)

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Новая доска"),
                content=ft.Column(width=420, tight=True, controls=[title, description, preset]),
                actions=[ghost_button("Отмена", lambda _: self.close_dialog(dialog)), primary_button("Создать", create)],
            )
            self.open_dialog(dialog)

        board_cards = []
        for board in self.state.boards:
            header_controls: list[ft.Control] = [
                ft.Text(board["title"], size=17, weight=ft.FontWeight.W_600, expand=True)
            ]
            if self.is_board_owner(board):
                header_controls.append(
                    ft.PopupMenuButton(
                        icon=ft.Icons.MORE_VERT,
                        tooltip="Действия с доской",
                        items=[
                            ft.PopupMenuItem(
                                content="Редактировать",
                                icon=ft.Icons.EDIT,
                                on_click=lambda _, board=board: self.open_edit_board_dialog(board),
                            ),
                            ft.PopupMenuItem(
                                content="Удалить",
                                icon=ft.Icons.DELETE,
                                on_click=lambda _, board=board: self.open_delete_board_dialog(board),
                            ),
                        ],
                    )
                )
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
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.START,
                                controls=header_controls,
                            ),
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

    def open_edit_board_dialog(self, board: dict[str, Any]) -> None:
        if not self.is_board_owner(board):
            return
        title = text_field("Название")
        title.value = board["title"]
        description = text_field("Описание", multiline=True)
        description.value = board.get("description") or ""

        def save(_: ft.ControlEvent) -> None:
            if not title.value:
                show_error(self.page, "Введите название доски")
                return
            try:
                self.api.update_board(
                    board["id"],
                    {"title": title.value, "description": description.value or None},
                )
                self.close_dialog(dialog)
                if self.state.current_board_id == board["id"] and self.state.kanban is not None:
                    self.refresh_kanban()
                else:
                    self.load_boards()
            except ApiError as error:
                self.handle_api_error(error)

        title.on_submit = save
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Редактировать доску"),
            content=ft.Column(width=420, tight=True, controls=[title, description]),
            actions=[
                ghost_button("Отмена", lambda _: self.close_dialog(dialog)),
                primary_button("Сохранить", save, ft.Icons.SAVE),
            ],
        )
        self.open_dialog(dialog)

    def open_delete_board_dialog(self, board: dict[str, Any]) -> None:
        if not self.is_board_owner(board):
            return

        def delete(_: ft.ControlEvent) -> None:
            try:
                self.api.delete_board(board["id"])
                self.close_dialog(dialog)
                if self.state.current_board_id == board["id"]:
                    self.state.current_board_id = None
                    self.state.kanban = None
                    self.state.selected_card_id = None
                    self.state.filters = {}
                    self.card_panel_scroll_offset = 0.0
                    self.card_panel_has_unsaved_changes = False
                self.load_boards()
            except ApiError as error:
                self.handle_api_error(error)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Удалить доску"),
            content=ft.Text(f"Доска «{board['title']}» и все ее колонки, карточки и комментарии будут удалены."),
            actions=[
                ghost_button("Отмена", lambda _: self.close_dialog(dialog)),
                primary_button("Удалить", delete, ft.Icons.DELETE),
            ],
        )
        self.open_dialog(dialog)

