from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.auth.dependencies import require_admin
from app.db import get_db
from app.models.audit_log import AuditLog
from app.models.user import User

router = APIRouter(prefix="/admin/audit", tags=["Admin Audit"])

@router.get("")
def audit_logs(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    logs = db.query(AuditLog).filter(AuditLog.tenant_id == current_user.tenant_id).order_by(AuditLog.created_at.desc()).limit(200).all()
    return logs
