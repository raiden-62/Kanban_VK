from __future__ import annotations

import flet as ft

from frontend.app.api_client import ApiError
from frontend.app.components.common import ghost_button, primary_button, show_error, text_field
from frontend.app.flet_compat import border_all
from frontend.app.theme import PALETTE


class AuthViewMixin:
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

