import enum
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, Enum, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base

class PaymentMethod(str, enum.Enum):
    CASH = "CASH"
    CARD = "CARD"
    TRANSFER = "TRANSFER"

class CashEntry(Base):
    __tablename__ = "cash_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod), default=PaymentMethod.CASH)

    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    concept: Mapped[str] = mapped_column(Text, nullable=True)
    appointment_id: Mapped[int | None] = mapped_column(ForeignKey("appointments.id"), nullable=True)