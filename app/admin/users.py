from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.auth.dependencies import require_admin
from app.db import get_db
from app.models.user import User
from app.schemas.admin_user import AdminUserCreate, AdminUserUpdate
from app.security.audit import create_audit_log
from app.security.password import hash_password

router = APIRouter(prefix="/admin/users", tags=["Admin Users"])


@router.get("")
def list_users(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    users = (
        db.query(User)
        .filter(User.tenant_id == current_user.tenant_id)
        .order_by(User.id)
        .all()
    )
    return [
        {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at,
        }
        for user in users
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_user(
    request: AdminUserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=request.email,
        full_name=request.full_name,
        password_hash=hash_password(request.password),
        role=request.role,
        tenant_id=current_user.tenant_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    create_audit_log(
        db=db,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        action="user_created",
        resource_type="user",
        resource_id=user.id,
        details=f"Created tenant user {user.id} with role {user.role}",
    )
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
    }


@router.patch("/{user_id}")
def update_user(
    user_id: int,
    request: AdminUserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    target = db.get(User, user_id)
    if not target or target.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    changes = request.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No user fields provided")
    if target.id == current_user.id and ("role" in changes or "is_active" in changes):
        # Prevents an admin from locking the tenant out of its own administration.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can't change your own role or deactivate your own account",
        )

    details = []
    for field, value in changes.items():
        if getattr(target, field) != value:
            details.append(f"{field}: {getattr(target, field)} -> {value}")
            setattr(target, field, value)
    db.commit()
    db.refresh(target)
    if details:
        create_audit_log(
            db=db,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            action="user_updated",
            resource_type="user",
            resource_id=target.id,
            details="; ".join(details),
        )
    return {
        "id": target.id,
        "email": target.email,
        "full_name": target.full_name,
        "role": target.role,
        "is_active": target.is_active,
        "created_at": target.created_at,
    }
