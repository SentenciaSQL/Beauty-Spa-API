from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

class GalleryImage(Base):
    __tablename__ = "gallery_images"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str | None] = mapped_column(String(120), nullable=True)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    alt_text: Mapped[str | None] = mapped_column(String(200), nullable=True)

    sort_order: Mapped[int] = mapped_column(Integer, default=0, index=True)

    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    thumb_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                                                 onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_gallery_order", "sort_order", "id"),
    )
