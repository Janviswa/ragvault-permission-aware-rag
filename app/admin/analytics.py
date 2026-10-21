from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.analytics_buckets import RANGE_PATTERN, make_buckets
from app.auth.dependencies import require_admin
from app.db import get_db
from app.models.access_request import AccessRequest
from app.models.audit_log import AuditLog
from app.models.document import Document
from app.models.security_event import SecurityEvent
from app.models.user import User

router = APIRouter(prefix="/admin/analytics", tags=["Admin Analytics"])


@router.get("/summary")
def analytics_summary(
    range_key: str = Query("7d", alias="range", pattern=RANGE_PATTERN),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    tenant = current_user.tenant_id
    today_day = date.today()
    since_day, bucket_days, buckets, locate = make_buckets(range_key, today_day)
    since = datetime.combine(since_day, datetime.min.time())

    users = db.query(User).filter(User.tenant_id == tenant).all()
    documents_by_class = dict(
        db.query(Document.classification, func.count(Document.id))
        .filter(Document.tenant_id == tenant)
        .group_by(Document.classification)
        .all()
    )
    pending_requests = (
        db.query(func.count(AccessRequest.id))
        .join(Document, AccessRequest.document_id == Document.id)
        .filter(AccessRequest.status == "pending", Document.tenant_id == tenant)
        .scalar()
    )
    # "open" = not looked at yet. Opening the Security page marks events as seen.
    open_events_by_severity = dict(
        db.query(SecurityEvent.severity, func.count(SecurityEvent.id))
        .filter(SecurityEvent.tenant_id == tenant, SecurityEvent.status == "open")
        .group_by(SecurityEvent.severity)
        .all()
    )

    audit_rows = (
        db.query(func.date(AuditLog.created_at), AuditLog.action, func.count(AuditLog.id))
        .filter(
            AuditLog.tenant_id == tenant,
            AuditLog.created_at >= since,
            AuditLog.action.in_(["rag_query", "document_accessed"]),
        )
        .group_by(func.date(AuditLog.created_at), AuditLog.action)
        .all()
    )
    event_rows = (
        db.query(func.date(SecurityEvent.created_at), func.count(SecurityEvent.id))
        .filter(SecurityEvent.tenant_id == tenant, SecurityEvent.created_at >= since)
        .group_by(func.date(SecurityEvent.created_at))
        .all()
    )

    today_totals = {"queries": 0, "document_views": 0, "security_events": 0}
    for day, action, count in audit_rows:
        key = "queries" if action == "rag_query" else "document_views"
        bucket = locate(day)
        if bucket:
            bucket[key] += count
        if str(day) == today_day.isoformat():
            today_totals[key] += count
    for day, count in event_rows:
        bucket = locate(day)
        if bucket:
            bucket["security_events"] += count
        if str(day) == today_day.isoformat():
            today_totals["security_events"] += count

    return {
        "totals": {
            "users": len(users),
            "active_users": sum(1 for user in users if user.is_active),
            "documents": sum(documents_by_class.values()),
            "pending_requests": pending_requests,
            "open_security_events": sum(open_events_by_severity.values()),
        },
        "users_by_role": {
            role: sum(1 for user in users if user.role == role)
            for role in ("Admin", "Manager", "Employee")
        },
        "documents_by_classification": documents_by_class,
        "open_events_by_severity": open_events_by_severity,
        "range": range_key,
        "bucket_days": bucket_days,
        "activity": buckets,
        "today": today_totals,
    }
