from pydantic import BaseModel, Field


class AccessRequestCreate(BaseModel):
    reason: str | None = Field(default=None, max_length=500)