from __future__ import annotations

from collections.abc import Callable
from typing import Any

import flet as ft

from frontend.app.api_client import ApiError
from frontend.app.components.common import ghost_button, primary_button, show_error, text_field
from frontend.app.components.kanban import label_chip
from frontend.app.flet_compat import border_all, sync_control_value
from frontend.app.theme import LABEL_COLORS, PALETTE, PRIORITY_LABELS, ROLE_LABELS


class DialogsMixin:
    def open_create_column_dialog(self, _: ft.ControlEvent) -> None:
        if not self.can_edit_current_board():
            return
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
        if not self.can_edit_current_board():
            return
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
        if not self.can_edit_current_board():
            return
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
        if not self.can_edit_current_board():
            return
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
        can_manage = self.can_manage_current_board()
        login = text_field("Логин пользователя")
        role = ft.Dropdown(
            label="Роль",
            value="viewer",
            options=[
                ft.dropdown.Option("editor", ROLE_LABELS["editor"]),
                ft.dropdown.Option("viewer", ROLE_LABELS["viewer"]),
            ],
        )
        role.on_select = sync_control_value

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

        def update_dialog_members() -> None:
            members = self.state.kanban.get("members", []) if self.state.kanban else []
            rows = [self.member_row(member, can_manage, update_dialog_members) for member in members]
            content_controls: list[ft.Control] = [*rows]
            if can_manage:
                content_controls.extend([ft.Divider(), login, role])
            dialog.content = ft.Column(width=480, tight=True, controls=content_controls)
            self.page.update()

        members = self.state.kanban.get("members", []) if self.state.kanban else []
        rows = [self.member_row(member, can_manage, update_dialog_members) for member in members]
        action_controls: list[ft.Control] = [ghost_button("Закрыть", lambda _: self.close_dialog(dialog))]
        if can_manage:
            action_controls.append(primary_button("Добавить", add_member))
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Участники"),
            content=ft.Column(
                width=480,
                tight=True,
                controls=[*rows, ft.Divider(), login, role] if can_manage else rows,
            ),
            actions=action_controls,
        )
        self.open_dialog(dialog)

    def member_row(
        self,
        member: dict[str, Any],
        can_manage: bool,
        on_members_changed: Callable[[], None] | None = None,
    ) -> ft.Row:
        role_name = ROLE_LABELS.get(member["role"], member["role"])
        user_id = member["user"]["id"]
        login = member["user"]["login"]

        if not can_manage or member["role"] == "owner":
            return ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(login, expand=True),
                    ft.Text(role_name, color=PALETTE.text_muted),
                ],
            )

        role_dropdown = ft.Dropdown(
            value=member["role"],
            width=150,
            options=[
                ft.dropdown.Option("editor", ROLE_LABELS["editor"]),
                ft.dropdown.Option("viewer", ROLE_LABELS["viewer"]),
            ],
        )

        def update_member_role(event: ft.ControlEvent) -> None:
            sync_control_value(event)
            try:
                updated_member = self.api.update_role(self.state.current_board_id, user_id, event.control.value)
                if self.state.kanban is not None:
                    self.state.kanban["members"] = [
                        updated_member if item["user"]["id"] == user_id else item
                        for item in self.state.kanban.get("members", [])
                    ]
                if on_members_changed is not None:
                    on_members_changed()
                else:
                    self.refresh_kanban()
            except ApiError as error:
                self.handle_api_error(error)

        def remove_member(_: ft.ControlEvent) -> None:
            try:
                self.api.delete_role(self.state.current_board_id, user_id)
                if self.state.kanban is not None:
                    self.state.kanban["members"] = [
                        item for item in self.state.kanban.get("members", []) if item["user"]["id"] != user_id
                    ]
                if on_members_changed is not None:
                    on_members_changed()
                else:
                    self.refresh_kanban()
            except ApiError as error:
                self.handle_api_error(error)

        role_dropdown.on_select = update_member_role
        role_dropdown.on_change = update_member_role
        return ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text(login, expand=True),
                role_dropdown,
                ft.IconButton(
                    icon=ft.Icons.PERSON_REMOVE,
                    tooltip="Убрать участника",
                    on_click=remove_member,
                ),
            ],
        )

    def open_labels_dialog(self, _: ft.ControlEvent) -> None:
        if not self.can_edit_current_board():
            return
        title = text_field("Название метки")
        selected_color = {"value": LABEL_COLORS[0]["color"]}
        swatches: list[ft.Container] = []

        def update_swatch_state() -> None:
            for swatch in swatches:
                is_selected = swatch.data == selected_color["value"]
                swatch.border = border_all(3 if is_selected else 1, PALETTE.text if is_selected else PALETTE.border)
                swatch.content = ft.Icon(ft.Icons.CHECK, color="white", size=16) if is_selected else None

        def select_color(color: str) -> None:
            selected_color["value"] = color
            update_swatch_state()
            self.page.update()

        def color_swatch(item: dict[str, str]) -> ft.Container:
            swatch = ft.Container(
                data=item["color"],
                width=32,
                height=32,
                bgcolor=item["color"],
                border_radius=16,
                alignment=ft.Alignment(0, 0),
                tooltip=item["title"],
                on_click=lambda _, color=item["color"]: select_color(color),
            )
            swatches.append(swatch)
            return swatch

        color_picker = ft.Row(
            wrap=True,
            spacing=8,
            run_spacing=8,
            controls=[color_swatch(item) for item in LABEL_COLORS],
        )
        update_swatch_state()

        def create(_: ft.ControlEvent) -> None:
            if not title.value or not selected_color["value"]:
                show_error(self.page, "Введите название и выберите цвет")
                return
            try:
                self.api.create_label(self.state.current_board_id, title.value, selected_color["value"])
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
                    ft.Text("Цвет", weight=ft.FontWeight.W_600),
                    color_picker,
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
        priority.on_select = sync_control_value
        label.on_select = sync_control_value
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
        self.focused_field_ids.add(id(dialog))
        self.attach_focus_tracking(dialog)
        self.page.show_dialog(dialog)

    def close_dialog(self, dialog: ft.AlertDialog) -> None:
        self.focused_field_ids.clear()
        self.page.pop_dialog()


