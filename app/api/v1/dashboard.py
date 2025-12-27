from __future__ import annotations

from datetime import date, datetime, time, timezone, timedelta
from zoneinfo import ZoneInfo
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_, desc

from app.core.db import get_db
from app.core.deps import require_roles
from app.core.config import settings

from app.models.cash import CashEntry
from app.models.appointment import Appointment, AppointmentStatus
from app.models.service import Service
from app.models.user import User

router = APIRouter(prefix="/dashboard")

TZ = ZoneInfo(settings.TIMEZONE)

def _local_date_range_to_utc(from_day: date, to_day: date) -> tuple[datetime, datetime]:
    """
    Convierte rango [from_day, to_day] (días locales) a datetimes UTC:
      start_utc = from_day 00:00 local -> UTC
      end_utc   = (to_day + 1) 00:00 local -> UTC  (exclusive)
    """
    start_local = datetime.combine(from_day, time.min).replace(tzinfo=TZ)
    end_local = datetime.combine(to_day, time.min).replace(tzinfo=TZ) + timedelta(days=1)
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)

def _pg_local_ts(col):
    """
    created_at (timestamptz) -> timestamp en zona local (sin tz) usando Postgres timezone()
    """
    return func.timezone(settings.TIMEZONE, col)

# ---------------------------
# 1) Summary: KPIs del rango
# ---------------------------
@router.get("/summary", dependencies=[Depends(require_roles("ADMIN"))])
def dashboard_summary(
    db: Session = Depends(get_db),
    from_day: date = Query(..., alias="from"),
    to_day: date = Query(..., alias="to"),
):
    if to_day < from_day:
        raise HTTPException(400, "to must be >= from")

    start_utc, end_utc = _local_date_range_to_utc(from_day, to_day)

    # Total ingresos (cash_entries)
    total_revenue = db.execute(
        select(func.coalesce(func.sum(CashEntry.amount), 0.0))
        .where(CashEntry.created_at >= start_utc, CashEntry.created_at < end_utc)
    ).scalar_one()

    # Cantidad de pagos (tickets)
    tickets = db.execute(
        select(func.count(CashEntry.id))
        .where(CashEntry.created_at >= start_utc, CashEntry.created_at < end_utc)
    ).scalar_one()

    avg_ticket = float(total_revenue) / tickets if tickets else 0.0

    # Citas por estado
    status_rows = db.execute(
        select(Appointment.status, func.count(Appointment.id))
        .where(Appointment.start_at >= start_utc, Appointment.start_at < end_utc)
        .group_by(Appointment.status)
    ).all()

    appt_by_status = {s.value if hasattr(s, "value") else str(s): c for (s, c) in status_rows}

    # Total citas en rango
    total_appts = sum(appt_by_status.values()) if appt_by_status else 0

    # Clientes nuevos en rango (solo CUSTOMER)
    new_customers = db.execute(
        select(func.count(User.id))
        .where(
            User.role == "CUSTOMER",
            User.created_at >= start_utc,
            User.created_at < end_utc,
        )
    ).scalar_one()

    return {
        "range": {"from": str(from_day), "to": str(to_day), "timezone": settings.TIMEZONE},
        "revenue_total": float(total_revenue),
        "tickets_count": int(tickets),
        "avg_ticket": float(avg_ticket),
        "appointments_total": int(total_appts),
        "appointments_by_status": appt_by_status,
        "new_customers": int(new_customers),
        "currency": settings.CURRENCY,
    }

# ---------------------------
# 2) Revenue daily
# ---------------------------
@router.get("/revenue/daily", dependencies=[Depends(require_roles("ADMIN"))])
def revenue_daily(
    db: Session = Depends(get_db),
    from_day: date = Query(..., alias="from"),
    to_day: date = Query(..., alias="to"),
):
    if to_day < from_day:
        raise HTTPException(400, "to must be >= from")

    start_utc, end_utc = _local_date_range_to_utc(from_day, to_day)

    day_key = func.date_trunc("day", _pg_local_ts(CashEntry.created_at))

    rows = db.execute(
        select(day_key.label("day"), func.coalesce(func.sum(CashEntry.amount), 0.0).label("total"))
        .where(CashEntry.created_at >= start_utc, CashEntry.created_at < end_utc)
        .group_by(day_key)
        .order_by(day_key.asc())
    ).all()

    items = [{"day": r.day.date().isoformat(), "total": float(r.total)} for r in rows]
    return {"from": str(from_day), "to": str(to_day), "items": items, "currency": settings.CURRENCY}

# ---------------------------
# 3) Revenue monthly (por año o rango)
# ---------------------------
@router.get("/revenue/monthly", dependencies=[Depends(require_roles("ADMIN"))])
def revenue_monthly(
    db: Session = Depends(get_db),
    year: int = Query(..., ge=2000, le=2100),
):
    # rango del año completo, en zona local
    start_local = datetime(year, 1, 1, tzinfo=TZ)
    end_local = datetime(year + 1, 1, 1, tzinfo=TZ)
    start_utc, end_utc = start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)

    month_key = func.date_trunc("month", _pg_local_ts(CashEntry.created_at))

    rows = db.execute(
        select(month_key.label("month"), func.coalesce(func.sum(CashEntry.amount), 0.0).label("total"))
        .where(CashEntry.created_at >= start_utc, CashEntry.created_at < end_utc)
        .group_by(month_key)
        .order_by(month_key.asc())
    ).all()

    items = [{"month": r.month.date().isoformat()[:7], "total": float(r.total)} for r in rows]  # YYYY-MM
    return {"year": year, "items": items, "currency": settings.CURRENCY}

# ---------------------------
# 4) Top services (por citas DONE o por pagos asociados a appointment)
# ---------------------------
@router.get("/top-services", dependencies=[Depends(require_roles("ADMIN"))])
def top_services(
    db: Session = Depends(get_db),
    from_day: date = Query(..., alias="from"),
    to_day: date = Query(..., alias="to"),
    limit: int = Query(10, ge=1, le=50),
):
    if to_day < from_day:
        raise HTTPException(400, "to must be >= from")

    start_utc, end_utc = _local_date_range_to_utc(from_day, to_day)

    # TOP por cantidad de citas DONE en rango (más consistente que pagos)
    rows = db.execute(
        select(Service.id, Service.name, func.count(Appointment.id).label("count"))
        .join(Appointment, Appointment.service_id == Service.id)
        .where(
            Appointment.start_at >= start_utc,
            Appointment.start_at < end_utc,
            Appointment.status == AppointmentStatus.DONE,
        )
        .group_by(Service.id, Service.name)
        .order_by(desc(func.count(Appointment.id)))
        .limit(limit)
    ).all()

    items = [{"service_id": r.id, "service_name": r.name, "count": int(r.count)} for r in rows]
    return {"from": str(from_day), "to": str(to_day), "items": items}

# ---------------------------
# 5) Employee workload (citas DONE / total por empleado)
# ---------------------------
@router.get("/employees/workload", dependencies=[Depends(require_roles("ADMIN"))])
def employees_workload(
    db: Session = Depends(get_db),
    from_day: date = Query(..., alias="from"),
    to_day: date = Query(..., alias="to"),
    limit: int = Query(50, ge=1, le=200),
):
    if to_day < from_day:
        raise HTTPException(400, "to must be >= from")

    start_utc, end_utc = _local_date_range_to_utc(from_day, to_day)

    rows = db.execute(
        select(
            User.id,
            User.first_name,
            User.last_name,
            func.count(Appointment.id).label("appointments"),
            func.sum(func.case((Appointment.status == AppointmentStatus.DONE, 1), else_=0)).label("done"),
        )
        .join(Appointment, Appointment.employee_user_id == User.id)
        .where(
            User.role == "EMPLOYEE",
            Appointment.start_at >= start_utc,
            Appointment.start_at < end_utc,
        )
        .group_by(User.id, User.first_name, User.last_name)
        .order_by(desc(func.count(Appointment.id)))
        .limit(limit)
    ).all()

    items = []
    for r in rows:
        items.append({
            "employee_user_id": r.id,
            "name": f"{r.first_name} {r.last_name}".strip(),
            "appointments": int(r.appointments),
            "done": int(r.done or 0),
        })

    return {"from": str(from_day), "to": str(to_day), "items": items}

# ---------------------------
# 6) Appointments time-series (por día) opcional para chart
# ---------------------------
@router.get("/appointments/daily", dependencies=[Depends(require_roles("ADMIN"))])
def appointments_daily(
    db: Session = Depends(get_db),
    from_day: date = Query(..., alias="from"),
    to_day: date = Query(..., alias="to"),
):
    if to_day < from_day:
        raise HTTPException(400, "to must be >= from")

    start_utc, end_utc = _local_date_range_to_utc(from_day, to_day)

    day_key = func.date_trunc("day", func.timezone(settings.TIMEZONE, Appointment.start_at))

    rows = db.execute(
        select(day_key.label("day"), func.count(Appointment.id).label("count"))
        .where(Appointment.start_at >= start_utc, Appointment.start_at < end_utc)
        .group_by(day_key)
        .order_by(day_key.asc())
    ).all()

    items = [{"day": r.day.date().isoformat(), "count": int(r.count)} for r in rows]
    return {"from": str(from_day), "to": str(to_day), "items": items}

@router.get("/revenue/by-method", dependencies=[Depends(require_roles("ADMIN"))])
def revenue_by_method(
    db: Session = Depends(get_db),
    from_day: date = Query(..., alias="from"),
    to_day: date = Query(..., alias="to"),
):
    if to_day < from_day:
        raise HTTPException(400, "to must be >= from")

    start_utc, end_utc = _local_date_range_to_utc(from_day, to_day)

    rows = db.execute(
        select(
            CashEntry.method,
            func.coalesce(func.sum(CashEntry.amount), 0.0).label("total"),
            func.count(CashEntry.id).label("count"),
        )
        .where(CashEntry.created_at >= start_utc, CashEntry.created_at < end_utc)
        .group_by(CashEntry.method)
        .order_by(CashEntry.method.asc())
    ).all()

    grand_total = sum(float(r.total) for r in rows) if rows else 0.0

    items = []
    for r in rows:
        method = r.method.value if hasattr(r.method, "value") else str(r.method)
        total = float(r.total)
        items.append({
            "method": method,                  # CASH | TRANSFER | CARD
            "total": total,
            "count": int(r.count),
            "share": (total / grand_total) if grand_total > 0 else 0.0,  # 0..1
        })

    return {
        "from": str(from_day),
        "to": str(to_day),
        "currency": settings.CURRENCY,
        "grand_total": float(grand_total),
        "items": items,
    }
