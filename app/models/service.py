from datetime import datetime, timezone
from sqlalchemy import String, Integer, Numeric, Boolean, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base

class Service(Base):
    __tablename__ = 'services'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer)
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc),
                                                 onupdate=datetime.now(timezone.utc))
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)