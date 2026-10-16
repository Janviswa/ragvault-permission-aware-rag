from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: int
    title: str
    file_name: str
    tenant_id: str
    classification: str
    created_at: datetime

    class Config:
        from_attributes = True