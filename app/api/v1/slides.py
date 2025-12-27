from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, func

from app.core.db import get_db
from app.core.deps import require_roles
from app.core.media import save_image_replace_and_thumb
from app.models.slide import Slide
from app.schemas.slide import SlideCreate, SlideUpdate, SlideOut, SlideReorderRequest

router = APIRouter(prefix="/slides")

@router.post("", response_model=SlideOut, dependencies=[Depends(require_roles("ADMIN"))])
def create_slide(payload: SlideCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()

    if data.get("sort_order") is None:
        max_order = db.execute(select(func.max(Slide.sort_order))).scalar_one()
        data["sort_order"] = (max_order or 0) + 1

    slide = Slide(**data)
    db.add(slide)
    db.commit()
    db.refresh(slide)
    return slide

@router.get("", response_model=list[SlideOut], dependencies=[Depends(require_roles("ADMIN"))])
def list_slides(
    db: Session = Depends(get_db),
    is_active: bool | None = None,
    q: str | None = None,
):
    stmt = select(Slide)

    if is_active is not None:
        stmt = stmt.where(Slide.is_active == is_active)

    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Slide.title.ilike(like), Slide.subtitle.ilike(like)))

    stmt = stmt.order_by(Slide.sort_order.asc(), Slide.id.asc())

    return db.execute(stmt).scalars().all()

@router.get("/{slide_id}", response_model=SlideOut, dependencies=[Depends(require_roles("ADMIN"))])
def get_slide(slide_id: int, db: Session = Depends(get_db)):
    slide = db.get(Slide, slide_id)
    if not slide:
        raise HTTPException(404, "Not found")
    return slide

@router.put("/{slide_id}", response_model=SlideOut, dependencies=[Depends(require_roles("ADMIN"))])
def update_slide(slide_id: int, payload: SlideUpdate, db: Session = Depends(get_db)):
    slide = db.get(Slide, slide_id)
    if not slide:
        raise HTTPException(404, "Not found")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(slide, k, v)

    db.commit()
    db.refresh(slide)
    return slide

@router.delete("/{slide_id}", dependencies=[Depends(require_roles("ADMIN"))])
def delete_slide(slide_id: int, db: Session = Depends(get_db)):
    slide = db.get(Slide, slide_id)
    if not slide:
        raise HTTPException(404, "Not found")

    # borrado: si quieres “soft delete”, cambia esto por is_active=False
    db.delete(slide)
    db.commit()
    return {"ok": True}

@router.post("/{slide_id}/image", dependencies=[Depends(require_roles("ADMIN"))])
def upload_slide_image(slide_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    slide = db.get(Slide, slide_id)
    if not slide:
        raise HTTPException(404, "Not found")

    image_url, thumb_url = save_image_replace_and_thumb(
        file=file,
        folder="slides",
        old_image_url=slide.image_url,
        old_thumb_url=slide.thumb_url,
        thumb_max_size=900,  # slides suelen ser más grandes
    )

    slide.image_url = image_url
    slide.thumb_url = thumb_url
    db.commit()
    db.refresh(slide)

    return {"id": slide.id, "image_url": slide.image_url, "thumb_url": slide.thumb_url}

@router.post("/reorder", dependencies=[Depends(require_roles("ADMIN"))])
def reorder_slides(payload: SlideReorderRequest, db: Session = Depends(get_db)):
    if not payload.items:
        return {"ok": True, "updated": 0}

    ids = [x.id for x in payload.items]
    # evitar ids duplicados
    if len(ids) != len(set(ids)):
        raise HTTPException(400, "Duplicate slide ids")

    slides = db.execute(select(Slide).where(Slide.id.in_(ids))).scalars().all()
    if len(slides) != len(ids):
        found = {s.id for s in slides}
        missing = [i for i in ids if i not in found]
        raise HTTPException(400, f"Missing slide ids: {missing}")

    # Si el cliente manda sort_order explícito lo usamos.
    # Si no, usamos el orden del array (0..n-1)
    id_to_order: dict[int, int] = {}
    for idx, item in enumerate(payload.items):
        id_to_order[item.id] = item.sort_order if item.sort_order is not None else idx

    for s in slides:
        s.sort_order = id_to_order[s.id]

    db.commit()
    return {"ok": True, "updated": len(slides)}
