from __future__ import annotations

from collections.abc import Callable

import flet as ft

from frontend.app.flet_compat import border_all, padding_symmetric
from frontend.app.theme import PALETTE, PRIORITY_LABELS, priority_color


def priority_chip(priority: str) -> ft.Container:
    color = priority_color(priority)
    return ft.Container(
        content=ft.Text(PRIORITY_LABELS.get(priority, priority), size=11, color="white"),
        bgcolor=color,
        border_radius=4,
        padding=padding_symmetric(horizontal=6, vertical=2),
    )


def label_chip(label: dict) -> ft.Container:
    return ft.Container(
        content=ft.Text(label["title"], size=11, color="white", no_wrap=True),
        bgcolor=label["color"],
        border_radius=4,
        padding=padding_symmetric(horizontal=6, vertical=2),
    )


def card_control(
    card: dict,
    on_open: Callable[[int], None],
    on_move_left: Callable[[dict], None],
    on_move_right: Callable[[dict], None],
) -> ft.Container:
    chips = [priority_chip(card.get("priority", "medium"))]
    chips.extend(label_chip(label) for label in card.get("labels", [])[:3])
    deadline = card.get("deadline")
    footer = []
    if deadline:
        footer.append(ft.Text(f"Дедлайн: {deadline}", size=12, color=PALETTE.text_muted))
    if card.get("assignee_id"):
        footer.append(ft.Text(f"Исполнитель #{card['assignee_id']}", size=12, color=PALETTE.text_muted))

    return ft.Container(
        data=card["id"],
        bgcolor=PALETTE.surface,
        border=border_all(1, PALETTE.border),
        border_radius=6,
        padding=10,
        on_click=lambda _: on_open(card["id"]),
        content=ft.Column(
            spacing=8,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Text(card["title"], size=14, weight=ft.FontWeight.W_600, expand=True),
                        ft.Row(
                            spacing=0,
                            controls=[
                                ft.IconButton(
                                    icon=ft.Icons.CHEVRON_LEFT,
                                    tooltip="Переместить влево",
                                    icon_size=16,
                                    on_click=lambda event: on_move_left(card),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.CHEVRON_RIGHT,
                                    tooltip="Переместить вправо",
                                    icon_size=16,
                                    on_click=lambda event: on_move_right(card),
                                ),
                            ],
                        ),
                    ],
                ),
                ft.Row(spacing=4, wrap=True, controls=chips),
                *footer,
            ],
        ),
    )


def column_control(
    column: dict,
    cards: list[dict],
    on_open_card: Callable[[int], None],
    on_add_card: Callable[[int], None],
    on_edit_column: Callable[[dict], None],
    on_delete_column: Callable[[dict], None],
    on_move_left: Callable[[dict], None],
    on_move_right: Callable[[dict], None],
) -> ft.GestureDetector:
    column_body = ft.Container(
        width=300,
        bgcolor=PALETTE.surface_muted,
        border=border_all(1, PALETTE.border),
        border_radius=8,
        padding=10,
        content=ft.Column(
            spacing=10,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(column["title"], size=15, weight=ft.FontWeight.W_600, expand=True),
                        ft.Row(
                            spacing=0,
                            controls=[
                                ft.IconButton(
                                    icon=ft.Icons.ADD,
                                    tooltip="Добавить карточку",
                                    on_click=lambda _: on_add_card(column["id"]),
                                ),
                                ft.PopupMenuButton(
                                    icon=ft.Icons.MORE_VERT,
                                    tooltip="Действия с колонкой",
                                    items=[
                                        ft.PopupMenuItem(
                                            content="Редактировать",
                                            icon=ft.Icons.EDIT,
                                            on_click=lambda _: on_edit_column(column),
                                        ),
                                        ft.PopupMenuItem(
                                            content="Удалить",
                                            icon=ft.Icons.DELETE,
                                            on_click=lambda _: on_delete_column(column),
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
                ft.Column(
                    spacing=8,
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        card_control(card, on_open_card, on_move_left, on_move_right)
                        for card in cards
                    ],
                ),
            ],
        ),
    )
    return ft.GestureDetector(
        content=column_body,
        on_secondary_tap=lambda _: on_edit_column(column),
    )
