
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from app.core.deps import get_current_user, require_roles
from app.core.pagination import paginate
from app.crud.scheduling_rules import assert_slot_is_valid
from app.models import PaymentMethod, CashEntry
from app.schemas.appointment import AppointmentCreate, AppointmentOut, AppointmentReschedule
from app.crud.appointments import create_appointment
from app.core.public_cache import public_cache
from app.schemas.appointment_done import AppointmentDoneOut
from app.schemas.appointment_stats import (
    AppointmentStatsOut, StatusCountOut, ServiceRevenueOut
)
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session, aliased
from app.core.config import settings
from app.core.db import get_db
from app.schemas.pagination import Page
from app.schemas.appointment_list import AppointmentListItemOut
from app.models.appointment import Appointment, AppointmentStatus
from app.models.user import User, Role
from app.models.service import Service
from app.integrations.whatsapp import whatsapp

router = APIRouter(prefix="/appointments")

@router.post("", response_model=AppointmentOut, dependencies=[Depends(require_roles("CUSTOMER"))])
def request_appointment(payload: AppointmentCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        appt = create_appointment(
            db=db,
            customer_user_id=user.id,
            service_id=payload.service_id,
            employee_user_id=payload.employee_user_id,
            start_at=payload.start_at,
            notes=payload.notes,
            step_minutes=payload.step_minutes or 15,
        )

        public_cache.delete_prefix("pub:avail:")

        return appt
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.post("/{appointment_id}/validate", response_model=AppointmentOut, dependencies=[Depends(require_roles("RECEPTIONIST","ADMIN"))])
def validate_appointment(appointment_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    appt = db.get(Appointment, appointment_id)
    if not appt:
        raise HTTPException(404, "Not found")
    if appt.status != AppointmentStatus.REQUESTED:
        raise HTTPException(400, "Invalid status transition")

    appt.status = AppointmentStatus.VALIDATED
    db.commit()
    db.refresh(appt)

    public_cache.delete_prefix("pub:avail:")

    customer = db.get(User, appt.customer_user_id)
    employee = db.get(User, appt.employee_user_id)
    service = db.get(Service, appt.service_id)

    if not service or not employee:
        # si esto pasa, hay data inconsistente
        raise HTTPException(500, "Appointment references missing employee/service")

    if customer and customer.whatsapp_opt_in and customer.phone_e164:
        background_tasks.add_task(
            whatsapp.send_template,
            to_e164=customer.phone_e164,
            template_name="spa_appt_validated",
            body_params=[
                customer.first_name,
                appt.start_at.strftime("%Y-%m-%d"),
                appt.start_at.strftime("%H:%M"),
                service.name,
                employee.first_name,
            ],
        )

    return appt

@router.post(
    "/{appointment_id}/confirm",
    response_model=AppointmentOut,
    dependencies=[Depends(require_roles("CUSTOMER", "RECEPTIONIST", "ADMIN"))],
)
def confirm_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    appt = db.get(Appointment, appointment_id)
    if not appt:
        raise HTTPException(404, "Not found")
    if appt.customer_user_id != user.id:
        raise HTTPException(403, "Forbidden")
    if appt.status != AppointmentStatus.VALIDATED:
        raise HTTPException(400, "Only VALIDATED appointments can be confirmed")

    service = db.get(Service, appt.service_id)
    if not service:
        raise HTTPException(400, "Service not found")

    # total pagado para esta cita
    paid_total = db.execute(
        select(func.coalesce(func.sum(CashEntry.amount), 0.0))
        .where(CashEntry.appointment_id == appt.id)
    ).scalar_one()

    # ajusta el nombre del campo si no es "price"
    service_price = float(service.price)

    required = service_price * 0.50
    if float(paid_total) < required:
        raise HTTPException(
            400,
            f"To confirm, you must pay at least 50% of the service price. "
            f"Required: {required:.2f} {settings.CURRENCY}, Paid: {float(paid_total):.2f} {settings.CURRENCY}"
        )

    appt.status = AppointmentStatus.CONFIRMED
    db.commit()
    db.refresh(appt)

    public_cache.delete_prefix("pub:avail:")

    return appt


@router.get("", response_model=Page[AppointmentOut])
def list_appointments(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),

    day: date | None = Query(default=None, description="YYYY-MM-DD (zona America/Santo_Domingo)"),
    status: AppointmentStatus | None = None,
    employee_user_id: int | None = None,
    customer_user_id: int | None = None,

    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    tz = ZoneInfo(settings.TIMEZONE)

    stmt = select(Appointment)

    # Scope por rol
    if user.role == Role.CUSTOMER:
        stmt = stmt.where(Appointment.customer_user_id == user.id)
    elif user.role == Role.EMPLOYEE:
        stmt = stmt.where(Appointment.employee_user_id == user.id)
    elif user.role in (Role.RECEPTIONIST, Role.ADMIN):
        # ven todo
        pass
    else:
        raise HTTPException(403, "Forbidden")

    # Filtros
    if status:
        stmt = stmt.where(Appointment.status == status)

    if employee_user_id:
        stmt = stmt.where(Appointment.employee_user_id == employee_user_id)

    if customer_user_id:
        stmt = stmt.where(Appointment.customer_user_id == customer_user_id)

    if day:
        start_day = datetime.combine(day, time(0, 0), tzinfo=tz)
        end_day = datetime.combine(day, time(23, 59, 59), tzinfo=tz)
        stmt = stmt.where(Appointment.start_at >= start_day).where(Appointment.start_at <= end_day)

    stmt = stmt.order_by(Appointment.start_at.asc())

    items, total = paginate(db, stmt, page, size)
    return Page[AppointmentOut](items=items, page=page, size=size, total=total)

@router.get("/list", response_model=Page[AppointmentListItemOut])
def list_appointments_view(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),

    # filtros de fecha
    day: date | None = Query(default=None, description="YYYY-MM-DD (si lo usas, ignora from/to)"),
    from_date: date | None = Query(default=None, alias="from", description="YYYY-MM-DD"),
    to_date: date | None = Query(default=None, alias="to", description="YYYY-MM-DD"),

    # otros filtros
    status: AppointmentStatus | None = None,
    employee_user_id: int | None = None,
    customer_user_id: int | None = None,

    # búsqueda
    q: str | None = Query(default=None, min_length=1, max_length=80),

    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    tz = ZoneInfo(settings.TIMEZONE)

    Employee = aliased(User)
    Customer = aliased(User)

    base = (
        select(
            Appointment.id,
            Appointment.start_at,
            Appointment.end_at,
            Appointment.status,
            Appointment.notes,

            Service.id.label("service_id"),
            Service.name.label("service_name"),

            Employee.id.label("employee_user_id"),
            Employee.first_name.label("employee_first_name"),
            Employee.last_name.label("employee_last_name"),

            Customer.id.label("customer_user_id"),
            Customer.first_name.label("customer_first_name"),
            Customer.last_name.label("customer_last_name"),
        )
        .join(Service, Service.id == Appointment.service_id)
        .join(Employee, Employee.id == Appointment.employee_user_id)
        .join(Customer, Customer.id == Appointment.customer_user_id)
    )

    # Scope por rol
    if user.role == Role.CUSTOMER:
        base = base.where(Appointment.customer_user_id == user.id)
    elif user.role == Role.EMPLOYEE:
        base = base.where(Appointment.employee_user_id == user.id)
    elif user.role in (Role.RECEPTIONIST, Role.ADMIN):
        pass
    else:
        raise HTTPException(403, "Forbidden")

    # Filtros
    if status:
        base = base.where(Appointment.status == status)
    if employee_user_id:
        base = base.where(Appointment.employee_user_id == employee_user_id)
    if customer_user_id:
        base = base.where(Appointment.customer_user_id == customer_user_id)

    # day tiene prioridad sobre rango
    if day:
        start_dt = datetime.combine(day, time(0, 0), tzinfo=tz)
        end_dt = datetime.combine(day, time(23, 59, 59), tzinfo=tz)
        base = base.where(Appointment.start_at >= start_dt).where(Appointment.start_at <= end_dt)
    else:
        if from_date:
            start_dt = datetime.combine(from_date, time(0, 0), tzinfo=tz)
            base = base.where(Appointment.start_at >= start_dt)
        if to_date:
            end_dt = datetime.combine(to_date, time(23, 59, 59), tzinfo=tz)
            base = base.where(Appointment.start_at <= end_dt)

        if from_date and to_date and from_date > to_date:
            raise HTTPException(400, "`from` cannot be after `to`")

    # Search q (cliente/empleado/servicio)
    if q:
        term = f"%{q.strip()}%"
        base = base.where(
            or_(
                Service.name.ilike(term),

                Customer.first_name.ilike(term),
                Customer.last_name.ilike(term),

                Employee.first_name.ilike(term),
                Employee.last_name.ilike(term),
            )
        )

    base = base.order_by(Appointment.start_at.asc())

    # Count total
    count_stmt = select(func.count()).select_from(base.subquery())
    total = db.execute(count_stmt).scalar_one()

    # Page
    rows = db.execute(
        base.offset((page - 1) * size).limit(size)
    ).mappings().all()

    items = [AppointmentListItemOut(**r) for r in rows]
    return {"items": items, "page": page, "size": size, "total": total}


@router.post("/{appointment_id}/cancel", response_model=AppointmentOut, dependencies=[Depends(require_roles("CUSTOMER", "RECEPTIONIST", "ADMIN"))])
def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    appt = db.get(Appointment, appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # Permisos:
    # - ADMIN / RECEPTIONIST pueden cancelar cualquiera
    # - CUSTOMER solo la suya (en cualquier momento, aunque falten 10 min)
    if user.role.value == "CUSTOMER" and appt.customer_user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    # No permitir cancelar estados finales
    if appt.status in (AppointmentStatus.DONE, AppointmentStatus.NO_SHOW):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel an appointment with status {appt.status}",
        )

    # Evitar doble cancelación
    if appt.status == AppointmentStatus.CANCELED:
        raise HTTPException(status_code=400, detail="Appointment already canceled")

    # Política: NO REEMBOLSO
    # Importante: NO borrar/modificar CashEntry asociados
    appt.status = AppointmentStatus.CANCELED
    db.commit()
    db.refresh(appt)

    public_cache.delete_prefix("pub:avail:")

    return appt

@router.post(
    "/{appointment_id}/no-show",
    response_model=AppointmentOut,
    dependencies=[Depends(require_roles("RECEPTIONIST", "ADMIN"))],
)
def mark_no_show(
    appointment_id: int,
    db: Session = Depends(get_db),
):
    appt = db.get(Appointment, appointment_id)
    if not appt:
        raise HTTPException(404, "Not found")

    # Solo tiene sentido si estaba confirmada
    if appt.status != AppointmentStatus.CONFIRMED:
        raise HTTPException(
            status_code=400,
            detail=f"Only CONFIRMED appointments can be marked as NO_SHOW (current: {appt.status})",
        )

    appt.status = AppointmentStatus.NO_SHOW
    db.commit()
    db.refresh(appt)

    public_cache.delete_prefix("pub:avail:")
    return appt

@router.post(
    "/{appointment_id}/done",
    response_model=AppointmentDoneOut,
    dependencies=[Depends(require_roles("RECEPTIONIST", "ADMIN"))],
)
def mark_done_hybrid(
    appointment_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    appt = db.get(Appointment, appointment_id)
    if not appt:
        raise HTTPException(404, "Not found")

    if appt.status != AppointmentStatus.CONFIRMED:
        raise HTTPException(
            400,
            f"Only CONFIRMED appointments can be marked DONE (current: {appt.status})",
        )

    appt.status = AppointmentStatus.DONE
    db.commit()
    db.refresh(appt)

    svc = db.get(Service, appt.service_id)
    if not svc:
        # raro, pero por seguridad
        raise HTTPException(500, "Service not found for appointment")

    suggestion = {
        "appointment_id": appt.id,
        "amount": float(svc.price),
        "method": PaymentMethod.CASH,
        "concept": f"Pago servicio: {svc.name}",
    }

    public_cache.delete_prefix("pub:avail:")

    return {"appointment": appt, "payment_suggestion": suggestion}

@router.get(
    "/stats",
    response_model=AppointmentStatsOut,
    dependencies=[Depends(require_roles("RECEPTIONIST", "ADMIN"))],
)
def appointment_stats(
    day: date | None = Query(default=None),
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),

    # qué estados cuentan para revenue estimado
    revenue_statuses: list[AppointmentStatus] = Query(
        default=[AppointmentStatus.CONFIRMED, AppointmentStatus.DONE]
    ),

    include_by_service: bool = Query(True),
    db: Session = Depends(get_db),
):
    tz = ZoneInfo(settings.TIMEZONE)

    # rango de fechas
    if day:
        start_dt = datetime.combine(day, time(0, 0), tzinfo=tz)
        end_dt = datetime.combine(day, time(23, 59, 59), tzinfo=tz)
    else:
        if from_date and to_date and from_date > to_date:
            raise HTTPException(400, "`from` cannot be after `to`")

        start_dt = datetime.combine(from_date, time(0, 0), tzinfo=tz) if from_date else None
        end_dt = datetime.combine(to_date, time(23, 59, 59), tzinfo=tz) if to_date else None

    def apply_range(stmt):
        if start_dt:
            stmt = stmt.where(Appointment.start_at >= start_dt)
        if end_dt:
            stmt = stmt.where(Appointment.start_at <= end_dt)
        return stmt

    # 1) total
    total_stmt = apply_range(select(func.count()).select_from(Appointment))
    total = db.execute(total_stmt).scalar_one()

    # 2) by_status
    by_status_stmt = apply_range(
        select(Appointment.status, func.count().label("cnt"))
        .group_by(Appointment.status)
    )
    rows = db.execute(by_status_stmt).all()
    by_status = [StatusCountOut(status=str(s), count=int(c)) for s, c in rows]

    # 3) revenue estimated = sum(service.price) de citas con estados seleccionados
    revenue_stmt = apply_range(
        select(func.coalesce(func.sum(Service.price), 0))
        .select_from(Appointment)
        .join(Service, Service.id == Appointment.service_id)
        .where(Appointment.status.in_(revenue_statuses))
    )
    revenue_estimated = float(db.execute(revenue_stmt).scalar_one() or 0)

    # 4) breakdown por servicio (opcional)
    by_service: list[ServiceRevenueOut] = []
    if include_by_service:
        svc_stmt = apply_range(
            select(
                Service.id,
                Service.name,
                func.count().label("cnt"),
                func.coalesce(func.sum(Service.price), 0).label("rev"),
            )
            .select_from(Appointment)
            .join(Service, Service.id == Appointment.service_id)
            .where(Appointment.status.in_(revenue_statuses))
            .group_by(Service.id, Service.name)
            .order_by(func.coalesce(func.sum(Service.price), 0).desc())
        )
        svc_rows = db.execute(svc_stmt).all()
        by_service = [
            ServiceRevenueOut(
                service_id=int(sid),
                service_name=str(name),
                count=int(cnt),
                revenue_estimated=float(rev),
            )
            for sid, name, cnt, rev in svc_rows
        ]

    return AppointmentStatsOut(
        total=total,
        by_status=by_status,
        revenue_estimated=revenue_estimated,
        by_service=by_service,
    )

@router.get("/me", dependencies=[Depends(require_roles("CUSTOMER"))])
def my_appointments(
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
    status: str | None = Query(default=None),
    from_: date | None = Query(default=None, alias="from"),
    to: date | None = Query(default=None),
):
    q = select(Appointment).where(Appointment.customer_user_id == user.id)

    if status:
        q = q.where(Appointment.status == status)

    tz = ZoneInfo(settings.TIMEZONE)
    if from_:
        q = q.where(Appointment.start_at >= datetime.combine(from_, time.min, tzinfo=tz))
    if to:
        q = q.where(Appointment.start_at <= datetime.combine(to, time.max, tzinfo=tz))

    q = q.order_by(Appointment.start_at.desc())

    items = db.execute(q).scalars().all()
    return {"items": items}

@router.post("/{appointment_id}/reschedule", dependencies=[Depends(require_roles("CUSTOMER"))])
def reschedule_appointment(
    appointment_id: int,
    payload: AppointmentReschedule,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    appt = db.get(Appointment, appointment_id)
    if not appt:
        raise HTTPException(404, "Not found")
    if appt.customer_user_id != user.id:
        raise HTTPException(403, "Forbidden")

    if appt.status not in [AppointmentStatus.REQUESTED, AppointmentStatus.VALIDATED]:
        raise HTTPException(400, "This appointment cannot be rescheduled")

    service = db.get(Service, appt.service_id)
    if not service:
        raise HTTPException(400, "Service not found")

    new_start = payload.start_at
    new_end = new_start + timedelta(minutes=service.duration_minutes)

    # Validación completa (horario + breaks + step + overlap)
    assert_slot_is_valid(
        db=db,
        employee_user_id=appt.employee_user_id,
        start_at=new_start,
        end_at=new_end,
        step_minutes=payload.step_minutes or 15,
        ignore_appointment_id=appt.id,  # importante para no chocar con sí misma
    )

    appt.start_at = new_start
    appt.end_at = new_end

    # opcional: si ya estaba VALIDATED/CONFIRMED, lo devuelves a REQUESTED
    # appt.status = AppointmentStatus.REQUESTED

    db.commit()
    db.refresh(appt)

    public_cache.delete_prefix("pub:avail:")

    return appt