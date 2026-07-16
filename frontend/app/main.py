from __future__ import annotations

import asyncio
import inspect
import os
import time
from typing import Any, Iterator

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
    KANBAN_REFRESH_INTERVAL_SECONDS = 3.0
    POLLING_SCROLL_PAUSE_SECONDS = 3.0

    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.api = ApiClient()
        self.state = AppState()
        self.focused_field_ids: set[int] = set()
        self.poll_refresh_in_progress = False
        self.polling_paused_until = 0.0
        self.card_panel_scroll_offset = 0.0
        self.pending_card_panel_scroll_control: ft.Column | None = None
        self.card_panel_has_unsaved_changes = False

        self.page.title = "VK Kanban"
        self.page.bgcolor = PALETTE.app_bg
        self.page.padding = 0
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.window_min_width = 1100
        self.page.window_min_height = 720

    def run(self) -> None:
        self.page.run_task(self.poll_kanban_updates)
        self.render_auth()

    def render(self, control: ft.Control) -> None:
        self.focused_field_ids.clear()
        self.attach_focus_tracking(control)
        self.page.controls.clear()
        self.page.add(control)
        self.page.update()
        self.restore_card_panel_scroll()

    def restore_card_panel_scroll(self) -> None:
        control = self.pending_card_panel_scroll_control
        self.pending_card_panel_scroll_control = None
        if control is None:
            return
        if self.card_panel_scroll_offset > 0:
            page = getattr(self, "page", None)
            if page is not None:
                page.run_task(self.restore_card_panel_scroll_async, control, self.card_panel_scroll_offset)
                return
            result = control.scroll_to(offset=self.card_panel_scroll_offset, duration=0)
            if inspect.isawaitable(result):
                result.close()

    async def restore_card_panel_scroll_async(self, control: ft.Column, offset: float) -> None:
        result = control.scroll_to(offset=offset, duration=0)
        if inspect.isawaitable(result):
            await result

    def iter_controls(self, control: Any) -> Iterator[Any]:
        if control is None or isinstance(control, str):
            return
        yield control

        child = getattr(control, "content", None)
        if child is not None:
            yield from self.iter_controls(child)

        for attr in ("controls", "items", "actions"):
            children = getattr(control, attr, None)
            if children:
                for child_control in children:
                    yield from self.iter_controls(child_control)

    def attach_focus_tracking(self, control: ft.Control) -> None:
        for item in self.iter_controls(control):
            if isinstance(item, (ft.TextField, ft.Dropdown, ft.Checkbox)):
                self.track_focusable_control(item)

    def track_focusable_control(self, control: ft.Control) -> None:
        original_focus = getattr(control, "on_focus", None)
        original_blur = getattr(control, "on_blur", None)

        def on_focus(event: ft.ControlEvent, original_handler: Any = original_focus) -> None:
            self.focused_field_ids.add(id(control))
            if original_handler is not None:
                original_handler(event)

        def on_blur(event: ft.ControlEvent, original_handler: Any = original_blur) -> None:
            self.focused_field_ids.discard(id(control))
            if original_handler is not None:
                original_handler(event)

        control.on_focus = on_focus
        control.on_blur = on_blur

    async def poll_kanban_updates(self) -> None:
        while True:
            await asyncio.sleep(self.KANBAN_REFRESH_INTERVAL_SECONDS)
            self.poll_current_board_once()

    def should_poll_current_board(self) -> bool:
        return (
            self.state.is_authenticated
            and self.state.current_board_id is not None
            and self.state.kanban is not None
            and not self.card_panel_has_unsaved_changes
            and not self.focused_field_ids
            and not self.poll_refresh_in_progress
            and time.monotonic() >= self.polling_paused_until
        )

    def pause_polling(self, seconds: float | None = None) -> None:
        pause_seconds = seconds if seconds is not None else self.POLLING_SCROLL_PAUSE_SECONDS
        self.polling_paused_until = max(self.polling_paused_until, time.monotonic() + pause_seconds)

    def poll_current_board_once(self) -> None:
        if not self.should_poll_current_board():
            return
        self.poll_refresh_in_progress = True
        try:
            self.state.kanban = self.api.get_kanban(self.state.current_board_id)
            if self.state.selected_card_id is not None and self.state.selected_card is None:
                self.state.selected_card_id = None
                self.card_panel_scroll_offset = 0.0
                self.card_panel_has_unsaved_changes = False
            self.render_board()
        except ApiError:
            return
        finally:
            self.poll_refresh_in_progress = False

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
        self.polling_paused_until = 0.0
        self.card_panel_scroll_offset = 0.0
        self.card_panel_has_unsaved_changes = False
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
