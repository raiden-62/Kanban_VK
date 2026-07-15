from __future__ import annotations

import os

import flet as ft

from frontend.app.api_client import ApiClient, ApiError
from frontend.app.components.common import show_error
from frontend.app.flet_compat import border_only, padding_symmetric
from frontend.app.state import AppState
from frontend.app.theme import PALETTE
from frontend.app.views.auth import AuthViewMixin
from frontend.app.views.board import BoardViewMixin
from frontend.app.views.boards import BoardsViewMixin
from frontend.app.views.dialogs import DialogsMixin


class KanbanFrontend(AuthViewMixin, BoardsViewMixin, BoardViewMixin, DialogsMixin):
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

    def app_bar(
        self,
        title: str,
        leading: ft.Control | None = None,
        actions: list[ft.Control] | None = None,
    ) -> ft.Container:
        controls: list[ft.Control] = []
        if leading is not None:
            controls.append(leading)
        controls.extend(
            [
                ft.Text(title, size=20, weight=ft.FontWeight.W_700, color=PALETTE.text),
                *(actions or []),
                ft.Container(expand=True),
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


def main(page: ft.Page) -> None:
    KanbanFrontend(page).run()


def app_view_from_env() -> ft.AppView:
    raw_view = os.getenv("KANBAN_FLET_VIEW")
    if not raw_view:
        return ft.AppView.FLET_APP
    normalized_view = raw_view.lower()
    for view in ft.AppView:
        if normalized_view in {view.name.lower(), view.value.lower()}:
            return view
    return ft.AppView.FLET_APP


if __name__ == "__main__":
    ft.run(
        main,
        host=os.getenv("KANBAN_FLET_HOST"),
        port=int(os.getenv("KANBAN_FLET_PORT", "0")),
        view=app_view_from_env(),
    )
