from enum import Enum


class BoardRole(str, Enum):
    owner = "owner"
    editor = "editor"
    viewer = "viewer"


class CardPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"
