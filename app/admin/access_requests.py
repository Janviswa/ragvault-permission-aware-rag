from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, Field, model_validator

from app.auth.dependencies import require_role
from app.db import get_db
from app.models.access_request import AccessRequest
from app.models.user import User
from app.models.document_permission import DocumentPermission
from app.models.document import Document
from app.models.audit_log import AuditLog
from app.access_decisions import decisions_for
from app.models.temporary_access import TemporaryAccess
from app.rag.ingestion import sync_document_permissions

router = APIRouter(
    prefix="/admin/access-requests",
    tags=["Admin Access Requests"],
)

MAX_TEMPORARY_HOURS = 24 * 90
MAX_TEMPORARY_DAYS_CUSTOM = 365


class ApproveBody(BaseModel):
    """Optional. Omit the body (or send {}) to approve permanently, like before.

    duration_hours: grant temporary access for that many hours from now.
    expires_at:     grant temporary access until a specific time (UTC if no zone is given).
    """

    duration_hours: int | None = Field(default=None, ge=1, le=MAX_TEMPORARY_HOURS)
    expires_at: datetime | None = None

    @model_validator(mode="after")
    def _one_or_none(self):
        if self.duration_hours is not None and self.expires_at is not None:
            raise ValueError("Send either duration_hours or expires_at, not both")
        return self


@router.get("")
def list_access_requests(
    status_filter: str = Query("pending", alias="status", pattern="^(pending|approved|rejected|all)$"),
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db),
):
    query = (
        db.query(AccessRequest, User, Document)
        .join(User, AccessRequest.user_id == User.id)
        .join(Document, AccessRequest.document_id == Document.id)
        .filter(
            User.tenant_id == current_user.tenant_id,
            Document.tenant_id == current_user.tenant_id,
        )
    )
    if status_filter != "all":
        query = query.filter(AccessRequest.status == status_filter)

    rows = query.order_by(AccessRequest.requested_at.desc()).limit(200).all()
    decisions = decisions_for(db, current_user.tenant_id, [r.id for r, _, _ in rows if r.status != "pending"])

    return [
        {
            "id": request.id,
            "user_id": request.user_id,
            "user_name": requester.full_name,
            "user_email": requester.email,
            "user_role": requester.role,
            "document_id": request.document_id,
            "document_title": document.title,
            "document_classification": document.classification,
            "status": request.status,
            "reason": request.reason,
            "requested_at": request.requested_at,
            "decided_at": request.decided_at,
            "decided_by": decisions.get(request.id, {}).get("decided_by"),
            "access_expires_at": decisions.get(request.id, {}).get("expires_at") if request.status == "approved" else None,
        }
        for request, requester, document in rows
    ]

@router.post("/{request_id}/approve")
def approve_access_request(
    request_id: int,
    body: ApproveBody | None = None,
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db),
):
    access_request = db.get(AccessRequest, request_id)

    if not access_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Access request not found",
        )

    if access_request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Access request is not pending",
        )

    document = db.get(Document, access_request.document_id)
    target_user = db.get(User, access_request.user_id)

    if not document or not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document or user not found",
        )

    if (
        current_user.tenant_id != document.tenant_id
        or target_user.tenant_id != document.tenant_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-tenant access denied",
        )

    # Work out whether this is a permanent grant or time-limited access.
    expires_at: datetime | None = None
    now = datetime.utcnow()
    if body and body.duration_hours:
        expires_at = now + timedelta(hours=body.duration_hours)
    elif body and body.expires_at:
        requested = body.expires_at
        requested = requested.replace(tzinfo=timezone.utc) if requested.tzinfo is None else requested.astimezone(timezone.utc)
        expires_at = requested.replace(tzinfo=None)
        if expires_at <= now:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Expiry must be in the future")
        if expires_at > now + timedelta(days=MAX_TEMPORARY_DAYS_CUSTOM):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Temporary access can't last longer than {MAX_TEMPORARY_DAYS_CUSTOM} days",
            )

    access_request.status = "approved"
    access_request.decided_at = now

    if expires_at:
        # Same mechanism as Documents -> Temporary access: the vector index is told now,
        # and the database check refuses the person once the time has passed.
        db.add(
            TemporaryAccess(
                user_id=access_request.user_id,
                document_id=access_request.document_id,
                granted_by=current_user.id,
                expires_at=expires_at,
            )
        )
    else:
        db.add(
            DocumentPermission(
                document_id=access_request.document_id,
                user_id=access_request.user_id,
                permission="read",
            )
        )
    db.commit()
    db.refresh(access_request)
    sync_document_permissions(db=db, document_id=document.id)

    audit_log = AuditLog(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        action="access_request_approved",
        resource_type="document",
        resource_id=str(access_request.document_id),
        status="allowed",
        details=(
            f"Access request {access_request.id} approved "
            f"for user {access_request.user_id}"
            + (f"; expires_at={expires_at.isoformat()}" if expires_at else "")
        ),
    )

    db.add(audit_log)
    db.commit()

    return {
        "message": "Access request approved",
        "expires_at": expires_at,
        "request_id": access_request.id,
        "document_id": access_request.document_id,
        "user_id": access_request.user_id,
        "status": access_request.status,
    }

@router.post("/{request_id}/reject")
def reject_access_request(
    request_id: int,
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db),
):
    access_request = db.get(AccessRequest, request_id)

    if not access_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Access request not found",
        )

    if access_request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Access request is not pending",
        )

    document = db.get(Document, access_request.document_id)
    target_user = db.get(User, access_request.user_id)

    if not document or not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document or user not found",
        )

    if (
        current_user.tenant_id != document.tenant_id
        or target_user.tenant_id != document.tenant_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-tenant access denied",
        )

    access_request.status = "rejected"
    access_request.decided_at = datetime.utcnow()

    db.commit()
    db.refresh(access_request)

    audit_log = AuditLog(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        action="access_request_rejected",
        resource_type="document",
        resource_id=str(access_request.document_id),
        status="allowed",
        details=(
            f"Access request {access_request.id} rejected "
            f"for user {access_request.user_id}"
        ),
    )

    db.add(audit_log)
    db.commit()

    return {
        "message": "Access request rejected",
        "request_id": access_request.id,
        "document_id": access_request.document_id,
        "user_id": access_request.user_id,
        "status": access_request.status,
    }