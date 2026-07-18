import flet as ft


def sync_control_value(event: ft.ControlEvent | None) -> None:
    if event is None:
        return
    control = getattr(event, "control", None)
    event_value = getattr(event, "data", None)
    if control is not None and event_value is not None:
        control.value = event_value


def border_all(width: int | float, color: str) -> ft.Border:
    side = ft.BorderSide(width=width, color=color)
    return ft.Border(top=side, right=side, bottom=side, left=side)


def border_only(
    *,
    top: ft.BorderSide | None = None,
    right: ft.BorderSide | None = None,
    bottom: ft.BorderSide | None = None,
    left: ft.BorderSide | None = None,
) -> ft.Border:
    return ft.Border(top=top, right=right, bottom=bottom, left=left)


def padding_symmetric(horizontal: int | float = 0, vertical: int | float = 0) -> ft.Padding:
    return ft.Padding(left=horizontal, right=horizontal, top=vertical, bottom=vertical)
