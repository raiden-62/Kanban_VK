from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CardPriority
from app.schemas.label import LabelRead


class CardBase(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    description: str | None = None
    assignee_id: int | None = None
    deadline: date | None = None
    priority: CardPriority = CardPriority.medium


class CardCreate(CardBase):
    column_id: int
    position: int | None = Field(default=None, ge=0)
    label_ids: list[int] = Field(default_factory=list)


class CardUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = None
    assignee_id: int | None = None
    deadline: date | None = None
    priority: CardPriority | None = None
    label_ids: list[int] | None = None


class CardMove(BaseModel):
    column_id: int
    position: int = Field(ge=0)


class CardRead(CardBase):
    id: int
    board_id: int
    column_id: int
    position: int
    created_at: datetime
    updated_at: datetime
    labels: list[LabelRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
