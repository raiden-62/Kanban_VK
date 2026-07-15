from __future__ import annotations

from typing import Callable

import flet as ft

from frontend.app.theme import PALETTE


def show_error(page: ft.Page, message: str) -> None:
    snack_bar = ft.SnackBar(
        content=ft.Text(message),
        bgcolor=PALETTE.danger,
        show_close_icon=True,
    )
    page.show_dialog(snack_bar)


def show_info(page: ft.Page, message: str) -> None:
    snack_bar = ft.SnackBar(
        content=ft.Text(message),
        bgcolor=PALETTE.primary,
        show_close_icon=True,
    )
    page.show_dialog(snack_bar)


def primary_button(text: str, on_click: Callable, icon: str | None = None) -> ft.Button:
    return ft.Button(
        content=text,
        icon=icon,
        on_click=on_click,
        bgcolor=PALETTE.primary,
        color="white",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
    )


def ghost_button(text: str, on_click: Callable, icon: str | None = None) -> ft.OutlinedButton:
    return ft.OutlinedButton(
        content=text,
        icon=icon,
        on_click=on_click,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
    )


def icon_button(icon: str, tooltip: str, on_click: Callable, color: str | None = None) -> ft.IconButton:
    return ft.IconButton(icon=icon, tooltip=tooltip, on_click=on_click, icon_color=color or PALETTE.text)


def text_field(label: str, password: bool = False, multiline: bool = False) -> ft.TextField:
    return ft.TextField(
        label=label,
        password=password,
        can_reveal_password=password,
        multiline=multiline,
        min_lines=3 if multiline else 1,
        border_radius=6,
    )


def panel_title(title: str) -> ft.Text:
    return ft.Text(title, size=18, weight=ft.FontWeight.W_600, color=PALETTE.text)
