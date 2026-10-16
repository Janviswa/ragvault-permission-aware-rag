from fastapi import HTTPException, status

from app.models.user import User


def verify_tenant_access(
    current_user: User,
    resource_tenant_id: str,
) -> None:
    if current_user.tenant_id != resource_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-tenant access denied",
        )