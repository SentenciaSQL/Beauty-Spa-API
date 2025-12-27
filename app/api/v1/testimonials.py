from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.core.db import get_db
from app.core.deps import require_roles
from app.core.media import save_image_replace_and_thumb
from app.models.testimonial import Testimonial
from app.schemas.testimonial import (
    TestimonialCreate, TestimonialUpdate, TestimonialOut,
    TestimonialReorderRequest
)

router = APIRouter(prefix="/testimonials")

@router.post("", response_model=TestimonialOut, dependencies=[Depends(require_roles("ADMIN"))])
def create_testimonial(payload: TestimonialCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()

    # sort_order automático: max + 1 si no viene
    if data.get("sort_order") is None:
        max_order = db.execute(select(func.max(Testimonial.sort_order))).scalar_one()
        data["sort_order"] = (max_order or 0) + 1

    t = Testimonial(**data)
    db.add(t)
    db.commit()
    db.refresh(t)
    return t

@router.get("", response_model=list[TestimonialOut], dependencies=[Depends(require_roles("ADMIN"))])
def list_testimonials(db: Session = Depends(get_db)):
    stmt = select(Testimonial).order_by(Testimonial.sort_order.asc(), Testimonial.id.asc())
    return db.execute(stmt).scalars().all()

@router.get("/{testimonial_id}", response_model=TestimonialOut, dependencies=[Depends(require_roles("ADMIN"))])
def get_testimonial(testimonial_id: int, db: Session = Depends(get_db)):
    t = db.get(Testimonial, testimonial_id)
    if not t:
        raise HTTPException(404, "Not found")
    return t

@router.put("/{testimonial_id}", response_model=TestimonialOut, dependencies=[Depends(require_roles("ADMIN"))])
def update_testimonial(testimonial_id: int, payload: TestimonialUpdate, db: Session = Depends(get_db)):
    t = db.get(Testimonial, testimonial_id)
    if not t:
        raise HTTPException(404, "Not found")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(t, k, v)

    db.commit()
    db.refresh(t)
    return t

@router.delete("/{testimonial_id}", dependencies=[Depends(require_roles("ADMIN"))])
def delete_testimonial(testimonial_id: int, db: Session = Depends(get_db)):
    t = db.get(Testimonial, testimonial_id)
    if not t:
        raise HTTPException(404, "Not found")

    db.delete(t)
    db.commit()
    return {"ok": True}

@router.post("/{testimonial_id}/image", dependencies=[Depends(require_roles("ADMIN"))])
def upload_testimonial_image(testimonial_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    t = db.get(Testimonial, testimonial_id)
    if not t:
        raise HTTPException(404, "Not found")

    image_url, thumb_url = save_image_replace_and_thumb(
        file=file,
        folder="testimonials",
        old_image_url=t.image_url,
        old_thumb_url=t.thumb_url,
        thumb_max_size=600,
    )

    t.image_url = image_url
    t.thumb_url = thumb_url
    db.commit()
    db.refresh(t)

    return {"id": t.id, "image_url": t.image_url, "thumb_url": t.thumb_url}

@router.post("/reorder", dependencies=[Depends(require_roles("ADMIN"))])
def reorder_testimonials(payload: TestimonialReorderRequest, db: Session = Depends(get_db)):
    if not payload.items:
        return {"ok": True, "updated": 0}

    ids = [x.id for x in payload.items]
    if len(ids) != len(set(ids)):
        raise HTTPException(400, "Duplicate ids")

    items = db.execute(select(Testimonial).where(Testimonial.id.in_(ids))).scalars().all()
    if len(items) != len(ids):
        found = {x.id for x in items}
        missing = [i for i in ids if i not in found]
        raise HTTPException(400, f"Missing ids: {missing}")

    id_to_order = {}
    for idx, it in enumerate(payload.items):
        id_to_order[it.id] = it.sort_order if it.sort_order is not None else idx

    for t in items:
        t.sort_order = id_to_order[t.id]

    db.commit()
    return {"ok": True, "updated": len(items)}
