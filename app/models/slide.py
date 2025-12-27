import enum
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, Boolean, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

class Slide(Base):
    __tablename__ = "slides"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(String(120))
    subtitle: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # si quieres: URL interna (/public/services) o absoluta (https://...)
    link_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    alt_text: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # orden para el slider (0..n). Más bajo = primero
    sort_order: Mapped[int] = mapped_column(Integer, default=0, index=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    # programación opcional
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    thumb_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                                                 onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_slides_active_order", "is_active", "sort_order"),
    )
