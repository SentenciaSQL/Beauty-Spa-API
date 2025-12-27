from datetime import datetime, date, timezone
from sqlalchemy import String, Text, DateTime, Integer, Index, Date
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

class Testimonial(Base):
    __tablename__ = "testimonials"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(120))
    message: Mapped[str] = mapped_column(Text)  # descripción / testimonio

    testimonial_date: Mapped[date] = mapped_column(Date)  # fecha simple

    # opcional (para UI con estrellitas)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)

    sort_order: Mapped[int] = mapped_column(Integer, default=0, index=True)

    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    thumb_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                                                 onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_testimonials_order", "sort_order", "id"),
    )
