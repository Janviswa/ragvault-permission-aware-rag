from pydantic import BaseModel, Field


class DocumentCreate(BaseModel):
    title: str
    file_name: str
    content: str | None = None
    classification: str = Field(default="Internal")