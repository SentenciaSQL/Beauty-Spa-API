from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.db import get_db
from app.core.deps import require_roles
from app.core.media import save_image_replace_and_thumb
from app.models.service import Service
from app.schemas.service import ServiceCreate, ServiceUpdate, ServiceOut

router = APIRouter(prefix="/services")

@router.get("", response_model=list[ServiceOut])
def list_services(db: Session = Depends(get_db)):
    return db.execute(select(Service).order_by(Service.name)).scalars().all()

@router.post("", response_model=ServiceOut, dependencies=[Depends(require_roles("ADMIN"))])
def create_service(payload: ServiceCreate, db: Session = Depends(get_db)):
    service = Service(**payload.model_dump())
    db.add(service)
    db.commit()
    db.refresh(service)
    return service

@router.patch("/{service_id}", response_model=ServiceOut, dependencies=[Depends(require_roles("ADMIN"))])
def update_service(service_id: int, payload: ServiceUpdate, db: Session = Depends(get_db)):
    service = db.get(Service, service_id)
    if not service:
        raise HTTPException(404, "Not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(service, key, value)
    db.commit()
    db.refresh(service)
    return service

@router.post("/{service_id}/image", dependencies=[Depends(require_roles("ADMIN"))])
def upload_service_image(service_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    svc = db.get(Service, service_id)
    if not svc:
        raise HTTPException(404, "Service not found")

    old_image = getattr(svc, "image_url", None)
    old_thumb = getattr(svc, "image_thumb_url", None)  # si no existe, None

    image_url, thumb_url = save_image_replace_and_thumb(
        file=file,
        folder="services",
        old_image_url=old_image,
        old_thumb_url=old_thumb,
        thumb_max_size=600,
    )

    svc.image_url = image_url
    if hasattr(svc, "image_thumb_url"):
        svc.image_thumb_url = thumb_url

    db.commit()
    db.refresh(svc)

    return {"id": svc.id, "image_url": image_url, "thumb_url": thumb_url}
