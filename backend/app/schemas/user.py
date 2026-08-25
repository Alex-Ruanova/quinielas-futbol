import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _validate_email(value: str) -> str:
    if "@" not in value or value.startswith("@") or value.endswith("@"):
        raise ValueError("email invalido")
    return value


class UserRegister(BaseModel):
    email: str
    password: str = Field(min_length=8)
    display_name: str = Field(min_length=1, max_length=255)
    phone: str | None = None
    contact_email: str | None = None

    _validate_email_field = field_validator("email")(_validate_email)


class UserLogin(BaseModel):
    email: str
    password: str


class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = None
    contact_email: str | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    display_name: str
    phone: str | None
    contact_email: str | None
    is_admin: bool
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
