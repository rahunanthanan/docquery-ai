"""Auth request/response schemas — backend validation rules from §6."""

import re
import uuid
from typing import Literal

from pydantic import ConfigDict, EmailStr, field_validator

from app.auth.models import UserRole
from app.core.schemas import CamelModel


class RegisterRequest(CamelModel):
    email: EmailStr
    password: str
    full_name: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        # §6: ≥ 10 chars, at least 1 letter and 1 number
        if len(value) < 10:
            raise ValueError("Password must be at least 10 characters long.")
        if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
            raise ValueError("Password must contain at least one letter and one number.")
        return value

    @field_validator("full_name")
    @classmethod
    def full_name_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped or len(stripped) > 100:
            raise ValueError("Full name must be 1–100 characters.")
        return stripped


class LoginRequest(CamelModel):
    email: EmailStr
    password: str


class UserOut(CamelModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool


class TokenResponse(CamelModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserOut
