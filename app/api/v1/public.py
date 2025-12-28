from datetime import date, datetime, timezone
from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from app.core.db import get_db
from app.core.pagination import paginate
from app.models import Slide, GalleryImage, Testimonial, Product, SiteSettings
from app.schemas.gallery import GalleryImageOut
from app.schemas.pagination import Page
from app.schemas.service import ServiceOut
from app.models.service import Service
from app.schemas.public import EmployeePublicOut
from app.models.user import User, Role
from app.crud.availability import get_employee_availability
from app.schemas.public_availability import AvailabilityByServiceOut, EmployeeSlotsOut
from app.schemas.public_availability_summary import (
    AvailabilitySummaryOut,
    EmployeeAvailabilitySummaryOut,
)
from app.core.public_cache import public_cache
from app.schemas.slide import SlideOut
from app.schemas.testimonial import TestimonialOut

router = APIRouter(prefix="/public", tags=["public"])

@router.get("/services", response_model=Page[ServiceOut])
def public_services(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Endpoint público para la web:
    - No requiere autenticación
    - Solo servicios activos
    - Paginado
    """
    stmt = (
        select(Service)
        .where(Service.is_active == True)  # noqa: E712
        .order_by(Service.name)
    )

    items, total = paginate(db, stmt, page, size)
    return Page[ServiceOut](items=items, page=page, size=size, total=total)

@router.get("/employees", response_model=Page[EmployeePublicOut])
def public_employees(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Público:
    - lista cosmetólogas (EMPLOYEE)
    - solo activos
    - paginado
    """
    stmt = (
        select(User)
        .where(User.role == Role.EMPLOYEE)
        .where(User.is_active == True)  # noqa: E712
        .order_by(User.first_name, User.last_name)
    )

    items, total = paginate(db, stmt, page, size)
    return Page[EmployeePublicOut](items=items, page=page, size=size, total=total)

@router.get("/availability/employees/{employee_user_id}")
def public_availability_for_employee(
    employee_user_id: int,
    day: date = Query(..., description="YYYY-MM-DD"),
    service_id: int = Query(...),
    step_minutes: int = Query(15, ge=5, le=60),
    db: Session = Depends(get_db),
):
    """
    Público:
    - devuelve slots disponibles para un empleado en una fecha
    - respeta horario negocio + breaks + citas existentes
    """
    employee = db.get(User, employee_user_id)
    if not employee or not employee.is_active or employee.role != Role.EMPLOYEE:
        raise HTTPException(404, "Employee not found")

    try:
        slots = get_employee_availability(db, employee_user_id, day, service_id, step_minutes)
        return {
            "employee_user_id": employee_user_id,
            "day": str(day),
            "service_id": service_id,
            "step_minutes": step_minutes,
            "slots": slots,
        }
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.get("/availability", response_model=AvailabilityByServiceOut)
def public_availability_by_service(
    day: date = Query(..., description="YYYY-MM-DD"),
    service_id: int = Query(...),
    step_minutes: int = Query(15, ge=5, le=60),
    db: Session = Depends(get_db),
):
    cache_key = f"pub:avail:detail:day={day}:service={service_id}:step={step_minutes}"

    def compute():
        service = db.get(Service, service_id)
        if not service or not service.is_active:
            raise HTTPException(404, "Service not found")

        employees = db.execute(
            select(User)
            .where(User.role == Role.EMPLOYEE)
            .where(User.is_active == True)  # noqa: E712
            .order_by(User.first_name, User.last_name)
        ).scalars().all()

        result = []
        for e in employees:
            slots = get_employee_availability(db, e.id, day, service_id, step_minutes)
            result.append(EmployeeSlotsOut(
                employee_user_id=e.id,
                first_name=e.first_name,
                last_name=e.last_name,
                slots=slots,
            ))

        return AvailabilityByServiceOut(
            day=str(day),
            service_id=service_id,
            step_minutes=step_minutes,
            employees=result,
        )

    return public_cache.get_or_set(cache_key, compute, ttl_seconds=60)

@router.get("/availability/summary", response_model=AvailabilitySummaryOut)
def public_availability_summary(
    day: date = Query(..., description="YYYY-MM-DD"),
    service_id: int = Query(...),
    step_minutes: int = Query(15, ge=5, le=60),
    preview_limit: int = Query(5, ge=0, le=20),
    db: Session = Depends(get_db),
):
    cache_key = f"pub:avail:summary:day={day}:service={service_id}:step={step_minutes}:preview={preview_limit}"

    def compute():
        service = db.get(Service, service_id)
        if not service or not service.is_active:
            # en cache no queremos guardar excepciones; lanzamos igual
            raise HTTPException(404, "Service not found")

        employees = db.execute(
            select(User)
            .where(User.role == Role.EMPLOYEE)
            .where(User.is_active == True)  # noqa: E712
            .order_by(User.first_name, User.last_name)
        ).scalars().all()

        out = []
        for e in employees:
            slots = get_employee_availability(db, e.id, day, service_id, step_minutes)
            out.append(EmployeeAvailabilitySummaryOut(
                employee_user_id=e.id,
                first_name=e.first_name,
                last_name=e.last_name,
                available_count=len(slots),
                preview_slots=slots[:preview_limit] if preview_limit > 0 else [],
            ))

        return AvailabilitySummaryOut(
            day=str(day),
            service_id=service_id,
            step_minutes=step_minutes,
            preview_limit=preview_limit,
            employees=out,
        )

    # cache TTL 60s (o cambia aquí a 30 si prefieres)
    return public_cache.get_or_set(cache_key, compute, ttl_seconds=60)

@router.get("/slides", response_model=list[SlideOut])
def public_slides(db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)

    stmt = (
        select(Slide)
        .where(Slide.is_active == True)
        .where(or_(Slide.starts_at.is_(None), Slide.starts_at <= now))
        .where(or_(Slide.ends_at.is_(None), Slide.ends_at >= now))
        .order_by(Slide.sort_order.asc(), Slide.id.asc())
    )

    return db.execute(stmt).scalars().all()

@router.get("/gallery", response_model=list[GalleryImageOut])
def public_gallery(db: Session = Depends(get_db)):
    stmt = select(GalleryImage).order_by(GalleryImage.sort_order.asc(), GalleryImage.id.asc())
    return db.execute(stmt).scalars().all()

@router.get("/testimonials", response_model=list[TestimonialOut])
def public_testimonials(db: Session = Depends(get_db)):
    stmt = select(Testimonial).order_by(Testimonial.sort_order.asc(), Testimonial.id.asc())
    return db.execute(stmt).scalars().all()

@router.get("/home")
def public_home(db: Session = Depends(get_db)):
    settings = db.execute(select(SiteSettings)).scalars().first()

    slides = db.execute(
        select(Slide)
        .where(Slide.is_active == True)
        .order_by(Slide.sort_order.asc(), Slide.id.asc())
        .limit(10)
    ).scalars().all()

    services = db.execute(
        select(Service)
        .where(Service.is_active == True)
        .order_by(Service.is_featured.desc(), Service.sort_order.asc(), Service.id.asc())
        .limit(12)
    ).scalars().all()

    products = db.execute(
        select(Product)
        .where(Product.is_active == True)
        .order_by(Product.is_featured.desc(), Product.sort_order.asc(), Product.id.asc())
        .limit(12)
    ).scalars().all()

    gallery = db.execute(
        select(GalleryImage)
        .order_by(GalleryImage.sort_order.asc(), GalleryImage.id.desc())
        .limit(18)
    ).scalars().all()

    testimonials = db.execute(
        select(Testimonial)
        .order_by(Testimonial.date.desc(), Testimonial.id.desc())
        .limit(10)
    ).scalars().all()

    return {
        "settings": settings,
        "slides": slides,
        "services": services,
        "products": products,
        "gallery": gallery,
        "testimonials": testimonials,
    }