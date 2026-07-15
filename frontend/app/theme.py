from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    app_bg: str = "#F4F7FB"
    surface: str = "#FFFFFF"
    surface_muted: str = "#EEF3F8"
    border: str = "#D8E1EA"
    text: str = "#17212B"
    text_muted: str = "#6B7A8A"
    primary: str = "#2787F5"
    primary_hover: str = "#1D74D6"
    danger: str = "#E64646"
    warning: str = "#F59E0B"
    success: str = "#22A06B"
    overdue_bg: str = "#FDECEC"
    overdue_text: str = "#B42318"
    low: str = "#7B8794"
    medium: str = "#2787F5"
    high: str = "#F59E0B"
    critical: str = "#E64646"


PALETTE = Palette()

PRIORITY_LABELS = {
    "low": "Низкий",
    "medium": "Средний",
    "high": "Высокий",
    "critical": "Критический",
}

ROLE_LABELS = {
    "owner": "Владелец",
    "editor": "Редактор",
    "viewer": "Наблюдатель",
}

LABEL_COLORS = [
    {"title": "Синий", "color": "#2787F5"},
    {"title": "Голубой", "color": "#18A0FB"},
    {"title": "Бирюзовый", "color": "#00A6A6"},
    {"title": "Зеленый", "color": "#22A06B"},
    {"title": "Лайм", "color": "#7CB342"},
    {"title": "Желтый", "color": "#F2C94C"},
    {"title": "Оранжевый", "color": "#F59E0B"},
    {"title": "Красный", "color": "#E64646"},
    {"title": "Розовый", "color": "#E91E63"},
    {"title": "Фиолетовый", "color": "#8E44AD"},
    {"title": "Индиго", "color": "#5B5FC7"},
    {"title": "Серый", "color": "#7B8794"},
]


def priority_color(priority: str | None) -> str:
    return getattr(PALETTE, priority or "medium", PALETTE.medium)
