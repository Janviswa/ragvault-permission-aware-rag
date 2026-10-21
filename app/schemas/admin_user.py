from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AdminUserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=255)
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=12, max_length=1024)
    role: Literal["Employee", "Manager", "Admin"] = "Employee"


class AdminUserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    role: Literal["Employee", "Manager", "Admin"] | None = None
    is_active: bool | None = None
