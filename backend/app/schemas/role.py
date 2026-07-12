from pydantic import BaseModel, ConfigDict

from app.models.enums import BoardRole
from app.schemas.user import UserRead


class RoleCreate(BaseModel):
    login: str
    role: BoardRole


class RoleUpdate(BaseModel):
    role: BoardRole


class RoleRead(BaseModel):
    id: int
    board_id: int
    user_id: int
    role: BoardRole
    user: UserRead

    model_config = ConfigDict(from_attributes=True)

