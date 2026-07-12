from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CommentCreate(BaseModel):
    text: str = Field(min_length=1)


class CommentUpdate(BaseModel):
    text: str = Field(min_length=1)


class CommentRead(BaseModel):
    id: int
    card_id: int
    author_id: int
    text: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

