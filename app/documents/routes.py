from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.auth.dependencies import get_current_user, require_admin
from app.db import get_db
from app.models.document import Document
from app.models.temporary_access import TemporaryAccess
from app.models.document_permission import DocumentPermission
from app.models.access_request import AccessRequest
from app.models.user import User
from app.rag.ingestion import delete_document_vectors, ingest_document
from app.security.acl import check_document_access
from app.security.audit import create_audit_log
from app.rag.ingestion import sync_document_permissions

router = APIRouter(prefix="/documents", tags=["Documents"])
VALID_CLASSIFICATIONS = {"Public", "Internal", "Confidential", "Restricted"}

class DocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    file_name: str = Field(min_length=1, max_length=255)
    content: str | None = Field(default=None, max_length=10_000_000)
    classification: str = Field(default="Internal")


class DocumentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    file_name: str | None = Field(default=None, min_length=1, max_length=255)
    content: str | None = Field(default=None, max_length=10_000_000)
    classification: str | None = None

class DocumentResponse(BaseModel):
    id: int
    title: str
    file_name: str
    content: str | None
    tenant_id: str
    classification: str

class PermissionTarget(BaseModel):
    user_id: int | None = None
    role: str | None = None
    permission: str = Field(default="read", pattern="^read$")

class TemporaryAccessRequest(BaseModel):
    user_id: int = Field(gt=0)
    expires_at: datetime

@router.post("", response_model=DocumentResponse)
def create_document(request: DocumentCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    if request.classification not in VALID_CLASSIFICATIONS:
        raise HTTPException(status_code=400, detail="Invalid classification")
    document = Document(title=request.title, file_name=request.file_name, content=request.content, tenant_id=current_user.tenant_id, classification=request.classification)
    db.add(document)
    db.commit()
    db.refresh(document)
    ingest_document(db=db, document=document)
    create_audit_log(db, current_user.id, current_user.tenant_id, "document_created", "document", document.id)
    return document

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    check_document_access(db, current_user, document)
    create_audit_log(db, current_user.id, current_user.tenant_id, "document_accessed", "document", document.id)
    return document


@router.patch("/{document_id}", response_model=DocumentResponse)
def update_document(
    document_id: int,
    request: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Cross-tenant access denied")

    changes = request.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="No document fields provided")
    if "classification" in changes and changes["classification"] not in VALID_CLASSIFICATIONS:
        raise HTTPException(status_code=400, detail="Invalid classification")

    for field, value in changes.items():
        setattr(document, field, value)
    db.commit()
    db.refresh(document)

    if {"content", "title", "file_name", "classification"} & changes.keys():
        delete_document_vectors(document.id)
        ingest_document(db=db, document=document)

    create_audit_log(
        db,
        current_user.id,
        current_user.tenant_id,
        "document_updated",
        "document",
        document.id,
    )
    return document


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Cross-tenant access denied")

    delete_document_vectors(document.id)
    db.query(DocumentPermission).filter(
        DocumentPermission.document_id == document_id
    ).delete(synchronize_session=False)
    db.query(TemporaryAccess).filter(
        TemporaryAccess.document_id == document_id
    ).delete(synchronize_session=False)
    db.query(AccessRequest).filter(
        AccessRequest.document_id == document_id
    ).delete(synchronize_session=False)
    db.delete(document)
    db.commit()
    create_audit_log(
        db,
        current_user.id,
        current_user.tenant_id,
        "document_deleted",
        "document",
        document_id,
    )
    return {"message": "Document deleted", "document_id": document_id}

@router.post("/{document_id}/temporary-access")
def grant_temporary_access(document_id: int, request: TemporaryAccessRequest, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    document = db.get(Document, document_id)
    target = db.get(User, request.user_id)
    if not document or not target:
        raise HTTPException(status_code=404, detail="Document or user not found")
    if document.tenant_id != current_user.tenant_id or target.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Cross-tenant access denied")
    expires_at = request.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    else:
        expires_at = expires_at.astimezone(timezone.utc)
    if expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Expiry must be in the future")
    expires_at_utc = expires_at.replace(tzinfo=None)
    access = TemporaryAccess(user_id=target.id, document_id=document.id, granted_by=current_user.id, expires_at=expires_at_utc)
    db.add(access)
    db.commit()
    db.refresh(access)
    sync_document_permissions(db=db, document_id=document.id)
    create_audit_log(db, current_user.id, current_user.tenant_id, "temporary_access_granted", "document", document.id, details=f"Granted to user {target.id} until {expires_at_utc.isoformat()} UTC")
    return {"message": "Temporary access granted", "access_id": access.id, "expires_at": access.expires_at}

@router.get("")
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    now = datetime.utcnow()

    documents = (
        db.query(Document)
        .filter(Document.tenant_id == current_user.tenant_id)
        .all()
    )

    if current_user.role == "Admin":
        accessible_documents = documents
    else:
        accessible_documents = []

        for document in documents:
            try:
                check_document_access(db, current_user, document)
                accessible_documents.append(document)
            except HTTPException:
                continue

    return [
        {
            "id": document.id,
            "title": document.title,
            "file_name": document.file_name,
            "classification": document.classification,
            "created_at": document.created_at,
            "summary": " ".join((document.content or "")[:600].split())[:240],
            "word_count": len((document.content or "").split()),
        }
        for document in accessible_documents
    ]

@router.delete("/{document_id}/temporary-access/{access_id}")
def revoke_temporary_access(
    document_id: int,
    access_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    document = db.get(Document, document_id)
    access = db.get(TemporaryAccess, access_id)

    if not document or not access or access.document_id != document_id:
        raise HTTPException(status_code=404, detail="Temporary access not found")

    if document.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Cross-tenant access denied")

    target = db.get(User, access.user_id)

    db.delete(access)
    db.commit()

    sync_document_permissions(
        db=db,
        document_id=document_id,
    )

    create_audit_log(
        db,
        current_user.id,
        current_user.tenant_id,
        "temporary_access_revoked",
        "document",
        document.id,
        details=f"Revoked temporary access for user {target.id if target else access.user_id}",
    )

    return {
        "message": "Temporary access revoked",
        "document_id": document_id,
        "access_id": access_id,
    }