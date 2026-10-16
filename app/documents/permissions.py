from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.auth.dependencies import require_admin
from app.db import get_db
from app.models.document import Document
from app.models.document_permission import DocumentPermission
from app.models.user import User
from app.security.audit import create_audit_log
from app.rag.ingestion import sync_document_permissions

router = APIRouter(prefix="/documents", tags=["Document Permissions"])

class PermissionCreate(BaseModel):
    user_id: int | None = Field(default=None, gt=0)
    role: str | None = Field(default=None, min_length=1, max_length=50)
    permission: str = Field(default="read", pattern="^read$")


@router.get("/{document_id}/permissions")
def list_permissions(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Cross-tenant access denied")
    permissions = (
        db.query(DocumentPermission)
        .filter(DocumentPermission.document_id == document_id)
        .order_by(DocumentPermission.id)
        .all()
    )
    return [
        {
            "id": permission.id,
            "document_id": permission.document_id,
            "user_id": permission.user_id,
            "role": permission.role,
            "permission": permission.permission,
        }
        for permission in permissions
    ]

@router.post("/{document_id}/permissions")
def add_permission(document_id: int, request: PermissionCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Cross-tenant access denied")
    if (request.user_id is None) == (request.role is None):
        raise HTTPException(status_code=400, detail="Specify exactly one of user_id or role")
    if request.user_id is not None:
        target = db.get(User, request.user_id)
        if not target or target.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Target user is outside the tenant")
    permission = DocumentPermission(document_id=document_id, user_id=request.user_id, role=request.role, permission=request.permission)
    db.add(permission)
    db.commit()
    db.refresh(permission)
    sync_document_permissions(
        db=db,
        document_id=document_id,
    )
    create_audit_log(db, current_user.id, current_user.tenant_id, "document_permission_granted", "document_permission", permission.id, details=f"document={document_id}, user={request.user_id}, role={request.role}")
    return {"message": "Document permission added", "permission_id": permission.id, "document_id": document_id}

@router.delete("/{document_id}/permissions/{permission_id}")
def revoke_permission(
    document_id: int,
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    document = db.get(Document, document_id)
    permission = db.get(DocumentPermission, permission_id)

    if not document or not permission or permission.document_id != document_id:
        raise HTTPException(status_code=404, detail="Permission not found")

    if document.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=403,
            detail="Cross-tenant access denied",
        )

    document_id_for_sync = permission.document_id

    db.delete(permission)
    db.commit()

    sync_document_permissions(
        db=db,
        document_id=document_id_for_sync,
    )

    create_audit_log(
        db,
        current_user.id,
        current_user.tenant_id,
        "document_permission_revoked",
        "document_permission",
        permission_id,
        details=f"document={document_id}",
    )

    return {
        "message": "Document permission revoked",
        "permission_id": permission_id,
    }