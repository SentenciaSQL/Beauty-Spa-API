from datetime import datetime, timedelta, date, time
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.core.config import settings
from app.models.business_hours import BusinessHours, BreakBlock, Weekday
from app.models.appointment import Appointment, AppointmentStatus
from app.models.service import Service

ACTIVE_STATUSES = {
    AppointmentStatus.REQUESTED,
    AppointmentStatus.VALIDATED,
    AppointmentStatus.CONFIRMED,
}

def _weekday_enum(d: date) -> Weekday:
    # python weekday: Mon=0..Sun=6 -> Weekday: Mon=1..Sun=7
    return Weekday(d.weekday() + 1)

def _parse_hhmm(s: str) -> time:
    hh, mm = s.split(":")
    return time(int(hh), int(mm))

def get_employee_availability(
    db: Session,
    employee_user_id: int,
    day: date,
    service_id: int,
    step_minutes: int = 15,
):
    tz = ZoneInfo(settings.TIMEZONE)
    service = db.get(Service, service_id)
    if not service or not service.is_active:
        raise ValueError("Service not found/active")

    wd = _weekday_enum(day)
    hours = db.execute(select(BusinessHours).where(BusinessHours.weekday == wd)).scalar_one_or_none()
    if not hours or hours.is_closed:
        return []

    open_t = _parse_hhmm(hours.open_time)
    close_t = _parse_hhmm(hours.close_time)

    day_open = datetime.combine(day, open_t, tzinfo=tz)
    day_close = datetime.combine(day, close_t, tzinfo=tz)

    duration = timedelta(minutes=service.duration_minutes)
    step = timedelta(minutes=step_minutes)

    # breaks
    breaks = db.execute(select(BreakBlock).where(BreakBlock.weekday == wd)).scalars().all()
    break_ranges = []
    for b in breaks:
        bs = datetime.combine(day, _parse_hhmm(b.start_time), tzinfo=tz)
        be = datetime.combine(day, _parse_hhmm(b.end_time), tzinfo=tz)
        break_ranges.append((bs, be))

    # existing appointments for the day (active statuses)
    stmt = select(Appointment).where(
        and_(
            Appointment.employee_user_id == employee_user_id,
            Appointment.status.in_(list(ACTIVE_STATUSES)),
            Appointment.start_at < day_close,
            Appointment.end_at > day_open,
        )
    )
    appts = db.execute(stmt).scalars().all()
    appt_ranges = [(a.start_at, a.end_at) for a in appts]

    def overlaps(r1, r2):
        (s1, e1), (s2, e2) = r1, r2
        return s1 < e2 and e1 > s2

    slots = []
    cur = day_open
    while cur + duration <= day_close:
        candidate = (cur, cur + duration)

        bad = False
        for br in break_ranges:
            if overlaps(candidate, br):
                bad = True
                break
        if not bad:
            for ar in appt_ranges:
                if overlaps(candidate, ar):
                    bad = True
                    break

        if not bad:
            slots.append(cur.isoformat())

        cur += step

    return slots
