from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


class TemporaryAccess(Base):
    __tablename__ = "temporary_access"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id"),
        nullable=False,
        index=True,
    )

    granted_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    user = relationship(
        "User",
        foreign_keys=[user_id],
        backref="temporary_access",
    )

    granted_by_user = relationship(
        "User",
        foreign_keys=[granted_by],
    )

    document = relationship(
        "Document",
        backref="temporary_access",
    )