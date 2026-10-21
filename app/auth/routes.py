from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db import get_db
from app.models.user import User
from app.models.tenant import Tenant
from app.schemas.auth import ChangePasswordRequest, LoginRequest, ProfileUpdate, TokenResponse
from app.security.jwt import create_access_token
from app.security.audit import create_audit_log
from app.security.password import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_403_FORBIDDEN)
def register():
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Public registration is disabled; contact your tenant administrator",
    )


@router.post("/login", response_model=TokenResponse)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == data.email).first()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive",
        )

    token = create_access_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
        role=user.role,
    )

    return TokenResponse(access_token=token)


def _me_payload(user: User, db: Session) -> dict:
    tenant = db.query(Tenant).filter(Tenant.slug == user.tenant_id).first()
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "tenant_id": user.tenant_id,
        "tenant_name": tenant.name if tenant else user.tenant_id,
    }


@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _me_payload(current_user, db)


@router.patch("/me")
def update_me(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Let a person change their own display name (role and email stay admin-managed)."""
    if data.full_name != current_user.full_name:
        previous = current_user.full_name
        current_user.full_name = data.full_name
        db.commit()
        create_audit_log(
            db,
            current_user.id,
            current_user.tenant_id,
            "profile_updated",
            "user",
            current_user.id,
            details=f"full_name: {previous} -> {data.full_name}",
        )
    return _me_payload(current_user, db)


@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    if data.new_password == data.current_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from the current one",
        )
    current_user.password_hash = hash_password(data.new_password)
    db.commit()
    create_audit_log(
        db,
        current_user.id,
        current_user.tenant_id,
        "password_changed",
        "user",
        current_user.id,
    )
    return {"message": "Password updated"}
