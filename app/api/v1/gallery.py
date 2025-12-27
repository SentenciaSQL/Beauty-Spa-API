from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.core.db import get_db
from app.core.deps import require_roles
from app.core.media import save_image_replace_and_thumb
from app.models.gallery_image import GalleryImage
from app.schemas.gallery import (
    GalleryImageCreate, GalleryImageUpdate, GalleryImageOut,
    GalleryReorderRequest
)

router = APIRouter(prefix="/gallery")

@router.post("", response_model=GalleryImageOut, dependencies=[Depends(require_roles("ADMIN"))])
def create_gallery_image(payload: GalleryImageCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()

    # sort_order automático: max + 1 si no viene
    if data.get("sort_order") is None:
        max_order = db.execute(select(func.max(GalleryImage.sort_order))).scalar_one()
        data["sort_order"] = (max_order or 0) + 1

    item = GalleryImage(**data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.get("", response_model=list[GalleryImageOut], dependencies=[Depends(require_roles("ADMIN"))])
def list_gallery_images(db: Session = Depends(get_db)):
    stmt = select(GalleryImage).order_by(GalleryImage.sort_order.asc(), GalleryImage.id.asc())
    return db.execute(stmt).scalars().all()

@router.get("/{image_id}", response_model=GalleryImageOut, dependencies=[Depends(require_roles("ADMIN"))])
def get_gallery_image(image_id: int, db: Session = Depends(get_db)):
    item = db.get(GalleryImage, image_id)
    if not item:
        raise HTTPException(404, "Not found")
    return item

@router.put("/{image_id}", response_model=GalleryImageOut, dependencies=[Depends(require_roles("ADMIN"))])
def update_gallery_image(image_id: int, payload: GalleryImageUpdate, db: Session = Depends(get_db)):
    item = db.get(GalleryImage, image_id)
    if not item:
        raise HTTPException(404, "Not found")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(item, k, v)

    db.commit()
    db.refresh(item)
    return item

@router.delete("/{image_id}", dependencies=[Depends(require_roles("ADMIN"))])
def delete_gallery_image(image_id: int, db: Session = Depends(get_db)):
    item = db.get(GalleryImage, image_id)
    if not item:
        raise HTTPException(404, "Not found")

    # opcional: aquí también podrías borrar archivos (image_url/thumb_url)
    db.delete(item)
    db.commit()
    return {"ok": True}

@router.post("/{image_id}/image", dependencies=[Depends(require_roles("ADMIN"))])
def upload_gallery_image(image_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    item = db.get(GalleryImage, image_id)
    if not item:
        raise HTTPException(404, "Not found")

    image_url, thumb_url = save_image_replace_and_thumb(
        file=file,
        folder="gallery",
        old_image_url=item.image_url,
        old_thumb_url=item.thumb_url,
        thumb_max_size=800,  # galería: thumbnails un poco más grandes
    )

    item.image_url = image_url
    item.thumb_url = thumb_url
    db.commit()
    db.refresh(item)

    return {"id": item.id, "image_url": item.image_url, "thumb_url": item.thumb_url}

@router.post("/reorder", dependencies=[Depends(require_roles("ADMIN"))])
def reorder_gallery(payload: GalleryReorderRequest, db: Session = Depends(get_db)):
    if not payload.items:
        return {"ok": True, "updated": 0}

    ids = [x.id for x in payload.items]
    if len(ids) != len(set(ids)):
        raise HTTPException(400, "Duplicate ids")

    items = db.execute(select(GalleryImage).where(GalleryImage.id.in_(ids))).scalars().all()
    if len(items) != len(ids):
        found = {x.id for x in items}
        missing = [i for i in ids if i not in found]
        raise HTTPException(400, f"Missing ids: {missing}")

    id_to_order = {}
    for idx, it in enumerate(payload.items):
        id_to_order[it.id] = it.sort_order if it.sort_order is not None else idx

    for gi in items:
        gi.sort_order = id_to_order[gi.id]

    db.commit()
    return {"ok": True, "updated": len(items)}
