from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (Index("ix_prt_user_expires", "user_id", "expires_at"),)
