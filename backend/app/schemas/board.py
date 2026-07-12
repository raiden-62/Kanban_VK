from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BoardBase(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str | None = None


class BoardCreate(BoardBase):
    pass


class BoardUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None


class BoardRead(BoardBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

