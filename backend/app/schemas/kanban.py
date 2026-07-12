from pydantic import BaseModel

from app.schemas.board import BoardRead
from app.schemas.card import CardRead
from app.schemas.column import ColumnRead
from app.schemas.label import LabelRead
from app.schemas.role import RoleRead


class KanbanRead(BaseModel):
    board: BoardRead
    columns: list[ColumnRead]
    cards: list[CardRead]
    labels: list[LabelRead]
    members: list[RoleRead]
