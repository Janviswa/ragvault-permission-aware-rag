from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.security_event import SecurityEvent


def create_security_event(
    db: Session,
    event_type: str,
    severity: str = "medium",
    status: str = "open",
    user_id: int | None = None,
    tenant_id: str | None = None,
    details: str | None = None,
):
    cooldown = datetime.utcnow() - timedelta(seconds=60)

    existing_event = (
        db.query(SecurityEvent)
        .filter(
            SecurityEvent.event_type == event_type,
            SecurityEvent.severity == severity,
            SecurityEvent.status == status,
            SecurityEvent.user_id == user_id,
            SecurityEvent.tenant_id == tenant_id,
            SecurityEvent.details == details,
            SecurityEvent.created_at >= cooldown,
        )
        .first()
    )

    if existing_event:
        return existing_event

    event = SecurityEvent(
        event_type=event_type,
        severity=severity,
        status=status,
        user_id=user_id,
        tenant_id=tenant_id,
        details=details,
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return event
