from pydantic import BaseModel


class UploadResponse(BaseModel):
    message: str
    document_id: int
    title: str
    file_name: str
    classification: str
    chunks_created: int