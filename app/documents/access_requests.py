from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.auth.dependencies import get_current_user
from app.db import get_db
from app.models.access_request import AccessRequest
from app.models.document import Document
from app.models.user import User
from app.security.audit import create_audit_log

router = APIRouter(prefix="/documents", tags=["Access Requests"])

class AccessRequestCreate(BaseModel):
    reason: str | None = Field(default=None, max_length=1000)

@router.post("/{document_id}/access-request")
def request_access(document_id: int, request: AccessRequestCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Cross-tenant access denied")
    existing = db.query(AccessRequest).filter(AccessRequest.document_id == document_id, AccessRequest.user_id == current_user.id, AccessRequest.status == "pending").first()
    if existing:
        raise HTTPException(status_code=409, detail="Access request already pending")
    access_request = AccessRequest(user_id=current_user.id, document_id=document_id, status="pending", reason=request.reason)
    db.add(access_request)
    db.commit()
    db.refresh(access_request)
    create_audit_log(db, current_user.id, current_user.tenant_id, "access_request_submitted", "access_request", access_request.id)
    return {"message": "Access request submitted", "request_id": access_request.id}
