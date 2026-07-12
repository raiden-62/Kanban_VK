from pydantic import BaseModel, ConfigDict, Field, field_validator


def validate_hex_color(value: str) -> str:
    if not value.startswith("#"):
        raise ValueError("Color must be a hex value like #3B82F6")
    if len(value) not in {4, 7}:
        raise ValueError("Color must be #RGB or #RRGGBB")
    allowed = set("0123456789abcdefABCDEF")
    if any(char not in allowed for char in value[1:]):
        raise ValueError("Color must be a hex value")
    return value


class LabelBase(BaseModel):
    title: str = Field(min_length=1, max_length=60)
    color: str = Field(min_length=4, max_length=20)

    @field_validator("color")
    @classmethod
    def validate_color(cls, value: str) -> str:
        return validate_hex_color(value)


class LabelCreate(LabelBase):
    pass


class LabelUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=60)
    color: str | None = Field(default=None, min_length=4, max_length=20)

    @field_validator("color")
    @classmethod
    def validate_color(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return validate_hex_color(value)


class LabelRead(LabelBase):
    id: int
    board_id: int

    model_config = ConfigDict(from_attributes=True)
