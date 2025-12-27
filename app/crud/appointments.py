from datetime import timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.core.config import settings
from app.crud.scheduling_rules import assert_slot_is_valid
from app.models.appointment import Appointment, AppointmentStatus
from app.models.service import Service

ACTIVE_STATUSES = {
    AppointmentStatus.REQUESTED,
    AppointmentStatus.VALIDATED,
    AppointmentStatus.CONFIRMED,
}

def has_overlap(db: Session, employee_user_id: int, start_at, end_at) -> bool:
    # solape: start < existing_end AND end > existing_start
    stmt = select(Appointment.id).where(
        and_(
            Appointment.employee_user_id == employee_user_id,
            Appointment.status.in_(list(ACTIVE_STATUSES)),
            start_at < Appointment.end_at,
            end_at > Appointment.start_at,
        )
    ).limit(1)
    return db.execute(stmt).first() is not None

def create_appointment(
    db: Session,
    customer_user_id: int,
    service_id: int,
    employee_user_id: int,
    start_at,
    notes: str | None,
    step_minutes: int = 15,
):
    tz = ZoneInfo(settings.TIMEZONE)

    # Si viene sin TZ, asígnale la del negocio
    if start_at.tzinfo is None:
        start_at = start_at.replace(tzinfo=tz)
    else:
        # Si viene en UTC (Z), conviértelo a TZ del negocio
        start_at = start_at.astimezone(tz)

    # Quita segundos y microsegundos (evita 13:15:00.364)
    start_at = start_at.replace(second=0, microsecond=0)

    service = db.get(Service, service_id)
    if not service or not service.is_active:
        raise ValueError("Service not found/active")

    end_at = start_at + timedelta(minutes=service.duration_minutes)

    # VALIDACIÓN COMPLETA (horario + breaks + pasado + step + overlap)
    assert_slot_is_valid(
        db=db,
        employee_user_id=employee_user_id,
        start_at=start_at,
        end_at=end_at,
        step_minutes=step_minutes,
    )

    appt = Appointment(
        customer_user_id=customer_user_id,
        employee_user_id=employee_user_id,
        service_id=service_id,
        start_at=start_at,
        end_at=end_at,
        status=AppointmentStatus.REQUESTED,
        notes=notes,
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return appt
