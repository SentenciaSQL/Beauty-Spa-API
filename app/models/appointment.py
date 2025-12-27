import enum
from datetime import datetime, timezone
from sqlalchemy import DateTime, Enum, ForeignKey, String, Index, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db import Base
from app.models import User, Service


class AppointmentStatus(str, enum.Enum):
    REQUESTED = "REQUESTED"      # cliente crea
    VALIDATED = "VALIDATED"      # recepcionista valida
    CONFIRMED = "CONFIRMED"      # cliente confirma
    CANCELED = "CANCELED"
    NO_SHOW = "NO_SHOW"
    DONE = "DONE"

class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)

    customer_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    employee_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), index=True)

    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),
                                                 onupdate=func.now(), nullable=False)

    status: Mapped[AppointmentStatus] = mapped_column(Enum(AppointmentStatus), default=AppointmentStatus.REQUESTED, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_appt_employee_time", "employee_user_id", "start_at", "end_at"),
    )

    customer: Mapped[User] = relationship("User", foreign_keys=[customer_user_id])
    employee: Mapped[User] = relationship("User", foreign_keys=[employee_user_id])
    service: Mapped[Service] = relationship("Service", foreign_keys=[service_id])