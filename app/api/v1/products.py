from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.db import get_db
from app.core.deps import require_roles
from app.core.media import save_image_replace_and_thumb
from app.core.pagination import paginate
from app.models.product import Product
from app.schemas.pagination import Page
from app.schemas.product import ProductCreate, ProductUpdate, ProductOut

router = APIRouter(prefix="/products")

@router.get("", response_model=Page[ProductOut])
def list_products(
        page: int = Query(1, ge=1),
        size: int = Query(20, ge=1, le=100),
        include_inactive: bool = False,
        db: Session = Depends(get_db)
):
    query = select(Product).order_by(Product.name)
    if not include_inactive:
        query = query.where(Product.is_active == True)  # noqa: E712

    items, total = paginate(db, query, page, size)
    return {"items": items, "page": page, "size": size, "total": total}

@router.post("", response_model=ProductOut, dependencies=[Depends(require_roles("ADMIN"))])
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    # evita duplicados por nombre
    exists = db.execute(select(Product).where(Product.name == payload.name)).scalar_one_or_none()
    if exists:
        raise HTTPException(409, "Product name already exists")

    product = Product(**payload.model_dump(), is_active=True)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

@router.patch("/{product_id}", response_model=ProductOut, dependencies=[Depends(require_roles("ADMIN"))])
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)
    return product

@router.post("/{product_id}/image", dependencies=[Depends(require_roles("ADMIN"))])
def upload_product_image(product_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    p = db.get(Product, product_id)
    if not p:
        raise HTTPException(404, "Product not found")

    old_image = getattr(p, "image_url", None)
    old_thumb = getattr(p, "image_thumb_url", None)

    image_url, thumb_url = save_image_replace_and_thumb(
        file=file,
        folder="products",
        old_image_url=old_image,
        old_thumb_url=old_thumb,
        thumb_max_size=600,
    )

    p.image_url = image_url
    if hasattr(p, "image_thumb_url"):
        p.image_thumb_url = thumb_url

    db.commit()
    db.refresh(p)

    return {"id": p.id, "image_url": image_url, "thumb_url": thumb_url}
