from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship

from app.db import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)

    tenant_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    classification: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Internal",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    permissions = relationship(
        "DocumentPermission",
        backref="document",
        cascade="all, delete-orphan",
    )