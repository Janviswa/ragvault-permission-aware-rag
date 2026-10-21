"""Who decided an access request, and until when the approval lasts.

AccessRequest has no decided_by column (and existing databases can't be migrated by create_all),
so the decision is read back from the audit log entry written when an admin approves or rejects.
"""
import re
from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User

_EXPIRES = re.compile(r"expires_at=(\d{4}-\d{2}-\d{2}T[\d:.]+)")


def decisions_for(db: Session, tenant_id: str, request_ids: list[int]) -> dict[int, dict]:
    """Map request id -> {"decided_by": name | None, "expires_at": datetime | None}."""
    if not request_ids:
        return {}
    entries = (
        db.query(AuditLog, User)
        .join(User, AuditLog.user_id == User.id)
        .filter(
            AuditLog.tenant_id == tenant_id,
            AuditLog.action.in_(["access_request_approved", "access_request_rejected"]),
            or_(*[AuditLog.details.like(f"Access request {rid} %") for rid in request_ids]),
        )
        .order_by(AuditLog.id)
        .all()
    )
    out: dict[int, dict] = {}
    for entry, admin in entries:
        details = entry.details or ""
        for rid in request_ids:
            if details.startswith(f"Access request {rid} "):
                match = _EXPIRES.search(details)
                out[rid] = {
                    "decided_by": admin.full_name,
                    "expires_at": datetime.fromisoformat(match.group(1)) if match else None,
                }
    return out
