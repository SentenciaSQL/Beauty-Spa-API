from datetime import datetime, time, date
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.core.db import get_db
from app.core.deps import get_current_user, require_roles
from app.core.config import settings
from app.core.pagination import paginate
from app.models.cash import CashEntry
from app.models.appointment import Appointment, AppointmentStatus
from app.schemas.cash import CashEntryCreate, CashEntryOut, CashStatsOut
from app.schemas.pagination import Page

router = APIRouter(prefix="/cash")

@router.post("", response_model=CashEntryOut, dependencies=[Depends(require_roles("ADMIN","RECEPTIONIST"))])
def create_cash_entry(
    payload: CashEntryCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    # valida appointment si viene
    if payload.appointment_id is not None:
        appt = db.get(Appointment, payload.appointment_id)
        if not appt:
            raise HTTPException(400, "appointment_id not found")

    tz = ZoneInfo(settings.TIMEZONE)
    created_at = payload.created_at or datetime.now(tz)

    entry = CashEntry(
        created_at=created_at,
        created_by_user_id=user.id,
        amount=payload.amount,
        concept=payload.concept,
        appointment_id=payload.appointment_id,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

@router.get("", response_model=Page[CashEntryOut], dependencies=[Depends(require_roles("ADMIN","RECEPTIONIST"))])
def list_cash_entries(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    date_from: datetime | None = Query(default=None, description="ISO datetime"),
    date_to: datetime | None = Query(default=None, description="ISO datetime"),
    db: Session = Depends(get_db),
):
    query = select(CashEntry).order_by(CashEntry.created_at.desc())
    if date_from:
        query = query.where(CashEntry.created_at >= date_from)
    if date_to:
        query = query.where(CashEntry.created_at <= date_to)

    items, total = paginate(db, query, page, size)
    return {"items": items, "page": page, "size": size, "total": total}

@router.get("/summary")
def cash_summary(
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    _=Depends(require_roles("ADMIN","RECEPTIONIST")),
):
    # resumen simple (sin group-by para mantenerlo corto)
    query = select(CashEntry)
    if date_from:
        query = query.where(CashEntry.created_at >= date_from)
    if date_to:
        query = query.where(CashEntry.created_at <= date_to)

    rows = db.execute(query).scalars().all()
    total = float(sum(r.amount for r in rows))
    return {"currency": settings.CURRENCY, "count": len(rows), "total": total}

@router.post(
    "/entries",
    response_model=CashEntryOut,
    dependencies=[Depends(require_roles("RECEPTIONIST", "ADMIN"))],
)
def create_cash_entry(
    payload: CashEntryCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    appt = None
    if payload.appointment_id:
        appt = db.get(Appointment, payload.appointment_id)
        if not appt:
            raise HTTPException(404, "Appointment not found")

        # Recomendado: solo cobrar citas DONE
        if appt.status != AppointmentStatus.DONE:
            raise HTTPException(400, "Only DONE appointments can be paid")

        # Evitar doble pago
        exists = db.execute(
            select(CashEntry).where(CashEntry.appointment_id == appt.id)
        ).scalar_one_or_none()
        if exists:
            raise HTTPException(409, "This appointment already has a payment entry")

    entry = CashEntry(
        amount=payload.amount,
        method=payload.method,
        concept=payload.concept,          # (si tu campo se llama concept)
        created_by_user_id=user.id,
        appointment_id=payload.appointment_id,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

@router.get(
    "/stats",
    response_model=CashStatsOut,
    dependencies=[Depends(require_roles("RECEPTIONIST", "ADMIN"))],
)
def cash_stats(
    day: date | None = Query(default=None),
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    db: Session = Depends(get_db),
):
    tz = ZoneInfo(settings.TIMEZONE)

    if day:
        start_dt = datetime.combine(day, time(0, 0), tzinfo=tz)
        end_dt = datetime.combine(day, time(23, 59, 59), tzinfo=tz)
    else:
        if from_date and to_date and from_date > to_date:
            raise HTTPException(400, "`from` cannot be after `to`")
        start_dt = datetime.combine(from_date, time(0, 0), tzinfo=tz) if from_date else None
        end_dt = datetime.combine(to_date, time(23, 59, 59), tzinfo=tz) if to_date else None

    stmt = select(CashEntry)
    if start_dt:
        stmt = stmt.where(CashEntry.created_at >= start_dt)
    if end_dt:
        stmt = stmt.where(CashEntry.created_at <= end_dt)

    # total y count
    total_stmt = select(func.coalesce(func.sum(CashEntry.amount), 0)).select_from(stmt.subquery())
    total = float(db.execute(total_stmt).scalar_one() or 0)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    count = int(db.execute(count_stmt).scalar_one())

    # by_method
    by_method_stmt = select(CashEntry.method, func.coalesce(func.sum(CashEntry.amount), 0)).select_from(stmt.subquery()).group_by(CashEntry.method)
    rows = db.execute(by_method_stmt).all()
    by_method = {str(m): float(v) for m, v in rows}

    return CashStatsOut(total=total, by_method=by_method, count=count)