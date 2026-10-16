from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from datetime import datetime

from app.auth.dependencies import require_role
from app.db import get_db
from app.models.access_request import AccessRequest
from app.models.user import User
from app.models.document_permission import DocumentPermission
from app.models.document import Document
from app.models.audit_log import AuditLog
from app.rag.ingestion import sync_document_permissions

router = APIRouter(
    prefix="/admin/access-requests",
    tags=["Admin Access Requests"],
)


@router.get("")
def list_access_requests(
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db),
):
    requests = (
        db.query(AccessRequest)
        .join(User, AccessRequest.user_id == User.id)
        .join(Document, AccessRequest.document_id == Document.id)
        .filter(
            AccessRequest.status == "pending",
            User.tenant_id == current_user.tenant_id,
            Document.tenant_id == current_user.tenant_id,
        )
        .all()
    )

    return [
        {
            "id": request.id,
            "user_id": request.user_id,
            "document_id": request.document_id,
            "status": request.status,
            "reason": request.reason,
            "requested_at": request.requested_at,
        }
        for request in requests
    ]

@router.post("/{request_id}/approve")
def approve_access_request(
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

    permission = DocumentPermission(
        document_id=access_request.document_id,
        user_id=access_request.user_id,
        permission="read",
    )

    access_request.status = "approved"
    access_request.decided_at = datetime.utcnow()

    db.add(permission)
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
        ),
    )

    db.add(audit_log)
    db.commit()

    return {
        "message": "Access request approved",
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