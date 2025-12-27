from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)

    table_name: Mapped[str] = mapped_column(String(80), index=True)
    record_id: Mapped[int] = mapped_column(Integer, index=True)

    action: Mapped[str] = mapped_column(String(10))  # INSERT | UPDATE | DELETE

    actor_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    before: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_audit_table_record", "table_name", "record_id"),
    )
