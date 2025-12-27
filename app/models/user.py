import enum
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base

class Role(enum.Enum):
    ADMIN = "ADMIN"
    RECEPTIONIST = "RECEPTIONIST"
    EMPLOYEE = "EMPLOYEE"
    CUSTOMER = "CUSTOMER"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc),
                                                 onupdate=datetime.now(timezone.utc))
    phone_e164: Mapped[str | None] = mapped_column(String(20),nullable=True,index=True,)
    whatsapp_opt_in: Mapped[bool] = mapped_column(Boolean,default=False,nullable=False,)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
