from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.auth.dependencies import require_admin
from app.db import get_db
from app.models.security_event import SecurityEvent
from app.models.temporary_access import TemporaryAccess
from app.models.document import Document
from app.models.user import User

router = APIRouter(prefix="/admin/security", tags=["Admin Security"])

@router.get("/events")
def security_events(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    events = db.query(SecurityEvent).filter(SecurityEvent.tenant_id == current_user.tenant_id).order_by(SecurityEvent.created_at.desc()).limit(100).all()
    return events


@router.get("/temporary-access")
def temporary_access(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    grants = (
        db.query(TemporaryAccess)
        .join(Document, TemporaryAccess.document_id == Document.id)
        .join(User, TemporaryAccess.user_id == User.id)
        .filter(
            Document.tenant_id == current_user.tenant_id,
            User.tenant_id == current_user.tenant_id,
            TemporaryAccess.expires_at > datetime.utcnow(),
        )
        .order_by(TemporaryAccess.expires_at)
        .all()
    )
    return [
        {
            "id": grant.id,
            "document_id": grant.document_id,
            "document_title": grant.document.title,
            "user_id": grant.user_id,
            "user_email": grant.user.email,
            "granted_by": grant.granted_by,
            "expires_at": grant.expires_at,
            "created_at": grant.created_at,
        }
        for grant in grants
    ]
