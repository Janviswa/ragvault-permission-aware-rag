from app.models.audit_log import AuditLog

def create_audit_log(db, user_id, tenant_id, action, resource_type, resource_id=None, status="success", details=None):
    log = AuditLog(user_id=user_id, tenant_id=tenant_id, action=action, resource_type=resource_type, resource_id=str(resource_id) if resource_id is not None else None, status=status, details=details)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
