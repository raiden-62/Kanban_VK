from pydantic import BaseModel, ConfigDict, Field


class ColumnBase(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    is_done: bool = False


class ColumnCreate(ColumnBase):
    position: int | None = Field(default=None, ge=0)


class ColumnUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    position: int | None = Field(default=None, ge=0)
    is_done: bool | None = None


class ColumnRead(ColumnBase):
    id: int
    board_id: int
    position: int
    is_done: bool

    model_config = ConfigDict(from_attributes=True)
