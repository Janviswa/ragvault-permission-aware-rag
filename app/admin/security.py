from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.auth.dependencies import require_admin
from app.db import get_db
from app.models.security_event import SecurityEvent
from app.models.temporary_access import TemporaryAccess
from app.models.document import Document
from app.models.user import User
from app.rag.retrieval import search_documents
from app.security.acl import has_read_access
from app.security.audit import create_audit_log
from app.security.events import create_security_event

router = APIRouter(prefix="/admin/security", tags=["Admin Security"])

@router.get("/events")
def security_events(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    events = db.query(SecurityEvent).filter(SecurityEvent.tenant_id == current_user.tenant_id).order_by(SecurityEvent.created_at.desc()).limit(100).all()
    return events


@router.post("/events/acknowledge")
def acknowledge_security_events(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    """Mark every not-yet-seen event as seen. Called when an admin opens the Security page.

    Events are only ever marked within the admin's own tenant.
    """
    open_events = (
        db.query(SecurityEvent)
        .filter(SecurityEvent.tenant_id == current_user.tenant_id, SecurityEvent.status == "open")
        .all()
    )
    for event in open_events:
        event.status = "seen"
    db.commit()
    if open_events:
        create_audit_log(
            db,
            current_user.id,
            current_user.tenant_id,
            "security_events_reviewed",
            "security",
            details=f"count={len(open_events)}",
        )
    return {"acknowledged": len(open_events)}


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


MAX_LEAKAGE_PROBES = 60


@router.post("/leakage-test")
def leakage_test(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    """Probe the retrieval ACL filter with each non-admin user's own identity.

    For every document a user may not read, search using the document's title
    as the query and fail the test if the vector store returns any chunk of a
    document the user cannot read. This exercises the Qdrant pre-retrieval
    filter; the post-retrieval database check is a separate layer.
    """
    tenant = current_user.tenant_id
    users = (
        db.query(User)
        .filter(User.tenant_id == tenant, User.is_active.is_(True), User.role != "Admin")
        .order_by(User.id)
        .all()
    )
    documents = db.query(Document).filter(Document.tenant_id == tenant).order_by(Document.id).all()

    probes = 0
    capped = False
    leaks = []
    users_tested = 0
    for user in users:
        blocked = [d for d in documents if not has_read_access(db, user, d)]
        if not blocked:
            continue
        users_tested += 1
        blocked_ids = {d.id for d in blocked}
        for document in blocked:
            if probes >= MAX_LEAKAGE_PROBES:
                capped = True
                break
            probes += 1
            results = search_documents(
                query=document.title,
                tenant_id=tenant,
                user_id=user.id,
                role=user.role,
                limit=10,
            )
            for result in results:
                leaked_id = (result.payload or {}).get("document_id")
                if leaked_id in blocked_ids:
                    leaks.append(
                        {
                            "user_id": user.id,
                            "user_email": user.email,
                            "document_id": leaked_id,
                            "probe_document_id": document.id,
                        }
                    )
        if capped:
            break

    passed = not leaks
    if not passed:
        create_security_event(
            db,
            event_type="leakage_test_failed",
            severity="critical",
            user_id=current_user.id,
            tenant_id=tenant,
            details=f"{len(leaks)} unauthorized chunk(s) returned across {probes} probes",
        )
    create_audit_log(
        db,
        current_user.id,
        tenant,
        "leakage_test_run",
        "security",
        details=f"probes={probes}, users={users_tested}, leaks={len(leaks)}",
        status="success" if passed else "failed",
    )
    return {
        "ran_at": datetime.utcnow(),
        "passed": passed,
        "users_tested": users_tested,
        "probes": probes,
        "capped": capped,
        "leaks": leaks,
    }
