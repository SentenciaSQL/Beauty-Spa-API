from __future__ import annotations

from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import settings
from app.models.business_hours import BusinessHours, BreakBlock, Weekday
from app.models.appointment import Appointment, AppointmentStatus

ACTIVE_STATUSES = {
    AppointmentStatus.REQUESTED,
    AppointmentStatus.VALIDATED,
    AppointmentStatus.CONFIRMED,
}

def _weekday_enum(d: date) -> Weekday:
    return Weekday(d.weekday() + 1)  # Mon=1..Sun=7

def _parse_hhmm(s: str) -> time:
    hh, mm = s.split(":")
    return time(int(hh), int(mm))

def _overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and a_end > b_start

def _round_up_to_step(dt: datetime, step_minutes: int) -> datetime:
    # redondea hacia arriba al próximo step
    dt0 = dt.replace(second=0, microsecond=0)
    remainder = dt0.minute % step_minutes
    if remainder == 0:
        return dt0
    return dt0 + timedelta(minutes=(step_minutes - remainder))

def assert_slot_is_valid(
    db: Session,
    employee_user_id: int,
    start_at: datetime,
    end_at: datetime,
    step_minutes: int = 15,
) -> None:
    """
    Lanza ValueError con mensaje claro si el slot es inválido.
    - horario negocio + breaks
    - no en el pasado (si es hoy)
    - alineación a step
    - no overlap con citas existentes
    """
    tz = ZoneInfo(settings.TIMEZONE)

    # Normaliza a TZ del negocio si viene naive
    if start_at.tzinfo is None:
        start_at = start_at.replace(tzinfo=tz)
    if end_at.tzinfo is None:
        end_at = end_at.replace(tzinfo=tz)

    if end_at <= start_at:
        raise ValueError("Invalid time range")

    day = start_at.date()
    if end_at.date() != day:
        raise ValueError("Appointments must start and end the same day")

    # Alineación a step (solo permite iniciar en :00/:15/:30/:45 si step=15)
    if start_at.minute % step_minutes != 0 or start_at.second != 0 or start_at.microsecond != 0:
        raise ValueError(f"start_at must align to {step_minutes}-minute steps")

    # No permitir slots en el pasado (si es hoy)
    now = datetime.now(tz)
    if day == now.date():
        min_start = _round_up_to_step(now, step_minutes)
        if start_at < min_start:
            raise ValueError("Cannot book in the past")

    wd = _weekday_enum(day)
    hours = db.execute(select(BusinessHours).where(BusinessHours.weekday == wd)).scalar_one_or_none()
    if not hours or hours.is_closed:
        raise ValueError("Business is closed that day")

    open_dt = datetime.combine(day, _parse_hhmm(hours.open_time), tzinfo=tz)
    close_dt = datetime.combine(day, _parse_hhmm(hours.close_time), tzinfo=tz)

    if start_at < open_dt or end_at > close_dt:
        raise ValueError("Outside business hours")

    # breaks
    breaks = db.execute(select(BreakBlock).where(BreakBlock.weekday == wd)).scalars().all()
    for b in breaks:
        bs = datetime.combine(day, _parse_hhmm(b.start_time), tzinfo=tz)
        be = datetime.combine(day, _parse_hhmm(b.end_time), tzinfo=tz)
        if _overlaps(start_at, end_at, bs, be):
            raise ValueError("Overlaps with a break block")

    # overlap con citas existentes del empleado (activas)
    stmt = select(Appointment).where(
        Appointment.employee_user_id == employee_user_id,
        Appointment.status.in_(list(ACTIVE_STATUSES)),
        Appointment.start_at < end_at,
        Appointment.end_at > start_at,
    )
    exists = db.execute(stmt).first()
    if exists:
        raise ValueError("Time slot not available")
