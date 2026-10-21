from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.temporary_access import TemporaryAccess
from app.models.document import Document
from app.models.document_permission import DocumentPermission
from app.models.user import User
from app.security.events import create_security_event

def has_read_access(db: Session, current_user: User, document: Document) -> bool:
    """Side-effect-free read check (no security events, no exceptions)."""
    if current_user.tenant_id != document.tenant_id:
        return False
    if current_user.role == "Admin":
        return True
    temporary_access = db.query(TemporaryAccess).filter(TemporaryAccess.document_id == document.id, TemporaryAccess.user_id == current_user.id, TemporaryAccess.expires_at > datetime.utcnow()).first()
    if temporary_access:
        return True
    user_permission = db.query(DocumentPermission).filter(DocumentPermission.document_id == document.id, DocumentPermission.user_id == current_user.id, DocumentPermission.permission == "read").first()
    if user_permission:
        return True
    role_permission = db.query(DocumentPermission).filter(DocumentPermission.document_id == document.id, DocumentPermission.role == current_user.role, DocumentPermission.permission == "read").first()
    return role_permission is not None


def check_document_access(db: Session, current_user: User, document: Document) -> bool:
    if current_user.tenant_id != document.tenant_id:
        create_security_event(
            db,
            event_type="cross_tenant_document_access",
            severity="critical",
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            details=f"Document {document.id} belongs to another tenant",
        )
        raise HTTPException(status_code=403, detail="Cross-tenant access denied")
    if has_read_access(db, current_user, document):
        return True
    create_security_event(
        db,
        event_type="unauthorized_document_access",
        severity="high",
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        details=f"User attempted to access document {document.id}",
    )
    raise HTTPException(status_code=403, detail="Document access denied")
