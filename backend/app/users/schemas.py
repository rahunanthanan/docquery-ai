"""Admin user-management schemas (§4.2)."""

import uuid
from datetime import datetime

from pydantic import model_validator

from app.auth.models import UserRole
from app.core.schemas import CamelModel


class AdminUserOut(CamelModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class AdminUserListOut(CamelModel):
    items: list[AdminUserOut]
    total: int
    limit: int
    offset: int


class AdminUserPatch(CamelModel):
    role: UserRole | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def at_least_one_change(self) -> "AdminUserPatch":
        if self.role is None and self.is_active is None:
            raise ValueError("Provide role and/or isActive to update.")
        return self
