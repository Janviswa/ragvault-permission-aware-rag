from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import BadZipFile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from docx.opc.exceptions import PackageNotFoundError
from pypdf.errors import PdfReadError

from app.auth.dependencies import require_admin
from app.db import get_db
from app.models.document import Document
from app.models.user import User
from app.rag.ingestion import ingest_document
from app.rag.loaders import load_text
from app.security.audit import create_audit_log

from app.documents.upload_schemas import UploadResponse


router = APIRouter(prefix="/documents", tags=["Document Upload"])

SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def validate_extension(file_name: str) -> str:
    extension = Path(file_name).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported document type: {extension}")

    return extension


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="File name is required",
        )

    try:
        extension = validate_extension(file.filename)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    content = await file.read(MAX_FILE_SIZE + 1)

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size exceeds 10 MB limit",
        )

    try:
        with NamedTemporaryFile(
            suffix=extension,
            delete=True,
        ) as temp_file:
            temp_file.write(content)
            temp_file.flush()

            extracted_text = load_text(
                temp_file.name,
                extension,
            )

    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="Unable to decode text file as UTF-8",
        ) from exc
    except (BadZipFile, OSError, PackageNotFoundError, PdfReadError, ValueError) as exc:
        raise HTTPException(
            status_code=400,
            detail="Unable to parse uploaded document",
        ) from exc

    if not extracted_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Document is empty",
        )

    file_name = Path(file.filename.replace("\\", "/")).name
    document = Document(
        title=Path(file_name).stem,
        file_name=file_name,
        content=extracted_text,
        tenant_id=current_user.tenant_id,
        classification="Internal",
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    chunks_created = ingest_document(
        db=db,
        document=document,
    )

    create_audit_log(
        db=db,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        action="document_uploaded",
        resource_type="document",
        resource_id=document.id,
        details=f"file={file_name}",
    )

    return UploadResponse(
        message="Document uploaded and indexed successfully",
        document_id=document.id,
        title=document.title,
        file_name=document.file_name,
        classification=document.classification,
        chunks_created=chunks_created,
    )