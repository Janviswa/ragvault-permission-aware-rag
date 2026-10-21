from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.access_decisions import decisions_for
from app.analytics_buckets import RANGE_PATTERN, make_buckets
from app.auth.dependencies import get_current_user
from app.db import get_db
from app.models.access_request import AccessRequest
from app.models.audit_log import AuditLog
from app.models.chat import Chat
from app.models.document import Document
from app.models.security_event import SecurityEvent
from app.models.user import User
from app.security.acl import has_read_access

router = APIRouter(prefix="/me", tags=["Me"])


@router.get("/access-requests")
def my_access_requests(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """The caller's own access requests, with who can (or did) decide each one."""
    rows = (
        db.query(AccessRequest, Document)
        .join(Document, AccessRequest.document_id == Document.id)
        .filter(
            AccessRequest.user_id == current_user.id,
            Document.tenant_id == current_user.tenant_id,
        )
        .order_by(AccessRequest.requested_at.desc())
        .all()
    )

    admins = (
        db.query(User)
        .filter(User.tenant_id == current_user.tenant_id, User.role == "Admin", User.is_active.is_(True))
        .order_by(User.full_name)
        .all()
    )
    admin_names = [admin.full_name for admin in admins]
    decisions = decisions_for(db, current_user.tenant_id, [r.id for r, _ in rows if r.status != "pending"])

    return [
        {
            "id": request.id,
            "document_id": document.id,
            "document_title": document.title,
            "file_name": document.file_name,
            "classification": document.classification,
            "status": request.status,
            "reason": request.reason,
            "requested_at": request.requested_at,
            "decided_at": request.decided_at,
            "decided_by": decisions.get(request.id, {}).get("decided_by"),
            "access_expires_at": decisions.get(request.id, {}).get("expires_at") if request.status == "approved" else None,
            "approvers": admin_names if request.status == "pending" else [],
        }
        for request, document in rows
    ]


@router.get("/analytics")
def my_analytics(
    range_key: str = Query("7d", alias="range", pattern=RANGE_PATTERN),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """The caller's OWN activity (not the company's). Same chart shape as the admin summary."""
    today_day = date.today()
    since_day, bucket_days, buckets, locate = make_buckets(range_key, today_day)
    since = datetime.combine(since_day, datetime.min.time())

    rows = (
        db.query(func.date(AuditLog.created_at), AuditLog.action, func.count(AuditLog.id))
        .filter(
            AuditLog.user_id == current_user.id,
            AuditLog.tenant_id == current_user.tenant_id,
            AuditLog.created_at >= since,
            AuditLog.action.in_(["rag_query", "document_accessed"]),
        )
        .group_by(func.date(AuditLog.created_at), AuditLog.action)
        .all()
    )
    refused_rows = (
        db.query(func.date(SecurityEvent.created_at), func.count(SecurityEvent.id))
        .filter(
            SecurityEvent.user_id == current_user.id,
            SecurityEvent.tenant_id == current_user.tenant_id,
            SecurityEvent.created_at >= since,
        )
        .group_by(func.date(SecurityEvent.created_at))
        .all()
    )

    today_totals = {"queries": 0, "document_views": 0, "security_events": 0}
    for day, action, count in rows:
        key = "queries" if action == "rag_query" else "document_views"
        bucket = locate(day)
        if bucket:
            bucket[key] += count
        if str(day) == today_day.isoformat():
            today_totals[key] += count
    for day, count in refused_rows:
        bucket = locate(day)
        if bucket:
            bucket["security_events"] += count
        if str(day) == today_day.isoformat():
            today_totals["security_events"] += count

    documents = db.query(Document).filter(Document.tenant_id == current_user.tenant_id).all()
    readable = sum(1 for d in documents if current_user.role == "Admin" or has_read_access(db, current_user, d))
    request_counts = dict(
        db.query(AccessRequest.status, func.count(AccessRequest.id))
        .filter(AccessRequest.user_id == current_user.id)
        .group_by(AccessRequest.status)
        .all()
    )
    questions_total = (
        db.query(func.count(AuditLog.id))
        .filter(AuditLog.user_id == current_user.id, AuditLog.tenant_id == current_user.tenant_id, AuditLog.action == "rag_query")
        .scalar()
    )

    return {
        "scope": "me",
        "totals": {
            "documents": readable,
            "questions": questions_total,
            "chats": db.query(func.count(Chat.id)).filter(Chat.user_id == current_user.id).scalar(),
            "requests_pending": request_counts.get("pending", 0),
            "requests_approved": request_counts.get("approved", 0),
            "requests_rejected": request_counts.get("rejected", 0),
        },
        "range": range_key,
        "bucket_days": bucket_days,
        "activity": buckets,
        "today": today_totals,
    }
