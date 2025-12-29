from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.db import get_db
from app.core.deps import get_current_user, require_roles
from app.core.media import save_image_replace_and_thumb
from app.core.security import hash_password
from app.models.user import User, Role
from app.schemas.pagination import Page
from app.schemas.user import UserCreate, UserUpdate, UserOut
from app.core.pagination import paginate

router = APIRouter(prefix="/users")

def _parse_role(role: str) -> Role:
    try:
        return Role(role)
    except Exception:
        raise HTTPException(400, f"Invalid role: {role}")

@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user

@router.get("", response_model=Page[UserOut], dependencies=[Depends(require_roles("ADMIN","RECEPTIONIST"))])
def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    role: str | None = None,
    is_active: bool | None = None,
    db: Session = Depends(get_db),
):
    q = select(User).order_by(User.id.desc())
    if role:
        q = q.where(User.role == _parse_role(role))
    if is_active is not None:
        q = q.where(User.is_active == is_active)

    items, total = paginate(db, q, page, size)
    return {"items": items, "page": page, "size": size, "total": total}

@router.post("", response_model=UserOut, dependencies=[Depends(require_roles("ADMIN"))])
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    # evita duplicados
    exists = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if exists:
        raise HTTPException(409, "Email already exists")

    user = User(
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        hashed_password=hash_password(payload.password),
        phone_e164=payload.phone_e164,
        whatsapp_opt_in=True,
        position=payload.position,
        role=_parse_role(payload.role),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.patch("/{user_id}", response_model=UserOut, dependencies=[Depends(require_roles("ADMIN"))])
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")

    data = payload.model_dump(exclude_unset=True)
    if "password" in data:
        user.hashed_password = hash_password(data.pop("password"))
    for k, v in data.items():
        setattr(user, k, v)

    db.commit()
    db.refresh(user)
    return user

@router.post("/register", response_model=UserOut)
def register_customer(payload: UserCreate, db: Session = Depends(get_db)):
    """
    Registro público (para web pública luego).
    Forzamos role=CUSTOMER aunque el payload traiga otro.
    """
    exists = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if exists:
        raise HTTPException(409, "Email already exists")

    user = User(
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        hashed_password=hash_password(payload.password),
        phone_e164=payload.phone_e164,
        whatsapp_opt_in=True,
        role=Role.CUSTOMER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/{user_id}/image", dependencies=[Depends(require_roles("ADMIN"))])
def upload_employee_image(user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(404, "User not found")

    old_image = getattr(u, "image_url", None)
    old_thumb = getattr(u, "image_thumb_url", None)

    image_url, thumb_url = save_image_replace_and_thumb(
        file=file,
        folder="employees",
        old_image_url=old_image,
        old_thumb_url=old_thumb,
        thumb_max_size=600,
    )

    u.image_url = image_url
    if hasattr(u, "image_thumb_url"):
        u.image_thumb_url = thumb_url

    db.commit()
    db.refresh(u)

    return {"id": u.id, "image_url": image_url, "thumb_url": thumb_url}
