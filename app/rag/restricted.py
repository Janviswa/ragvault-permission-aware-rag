"""Detect when a question is best answered by a document the user cannot read.

The wireframe's "Access Restricted" reply needs to tell the user *which*
document they would need access to. Only metadata (title, file name,
classification, roles) leaves this module. Document text is never read here.
"""
from sqlalchemy.orm import Session

from app.config import settings
from app.models.document import Document
from app.models.document_permission import DocumentPermission
from app.models.user import User
from app.rag.retrieval import search_tenant_documents
from app.security.acl import has_read_access
from app.security.events import create_security_event


def required_roles_for(db: Session, document_id: int) -> list[str]:
    rows = (
        db.query(DocumentPermission.role)
        .filter(
            DocumentPermission.document_id == document_id,
            DocumentPermission.permission == "read",
            DocumentPermission.role.isnot(None),
        )
        .distinct()
        .all()
    )
    roles = sorted({role for (role,) in rows})
    # Admins can always read; with no role grants, Admin is the only role that can.
    return roles or ["Admin"]


def find_restricted_match(
    db: Session,
    current_user: User,
    question: str,
    authorized_results: list,
) -> dict | None:
    """Return metadata for a more relevant document the user may not read, else None."""
    if current_user.role == "Admin":
        return None

    best_authorized = max((result.score for result in authorized_results), default=0.0)

    for hit in search_tenant_documents(question, current_user.tenant_id, limit=5):
        if hit.score < settings.restricted_match_min_score or hit.score <= best_authorized:
            break  # hits are ordered by score; nothing further can qualify
        document_id = (hit.payload or {}).get("document_id")
        document = db.get(Document, document_id) if document_id else None
        if not document or document.tenant_id != current_user.tenant_id:
            continue
        if has_read_access(db, current_user, document):
            continue

        create_security_event(
            db,
            event_type="restricted_document_query",
            severity="medium",
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            details=f"Question matched document {document.id} which the user cannot read",
        )
        return {
            "document_id": document.id,
            "title": document.title,
            "file_name": document.file_name,
            "classification": document.classification,
            "required_roles": required_roles_for(db, document.id),
            "your_role": current_user.role,
        }
    return None
