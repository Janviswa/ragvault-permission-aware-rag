from pydantic import BaseModel


class DocumentPermissionCreate(BaseModel):
    user_id: int | None = None
    role: str | None = None
    permission: str = "read"
