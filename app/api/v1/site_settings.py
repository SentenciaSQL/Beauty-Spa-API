from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_roles
from app.models.site_settings import SiteSettings
from app.models.site_social_link import SiteSocialLink
from app.schemas.site_settings import SiteSettingsOut, SiteSettingsUpsert, SocialLinkIn, SocialLinkOut
from app.services.media import save_image_and_replace

router = APIRouter(prefix="/site-settings")

def _get_or_create_settings(db: Session) -> SiteSettings:
    st = db.execute(select(SiteSettings).limit(1)).scalar_one_or_none()
    if not st:
        st = SiteSettings(app_name="Spa App")
        db.add(st)
        db.commit()
        db.refresh(st)
    return st

# ADMIN: ver settings (incluye redes)
@router.get("", response_model=SiteSettingsOut, dependencies=[Depends(require_roles("ADMIN"))])
def get_settings(db: Session = Depends(get_db)):
    return _get_or_create_settings(db)

# ADMIN: upsert settings
@router.put("", response_model=SiteSettingsOut, dependencies=[Depends(require_roles("ADMIN"))])
def upsert_settings(payload: SiteSettingsUpsert, db: Session = Depends(get_db)):
    st = _get_or_create_settings(db)
    for k, v in payload.model_dump().items():
        setattr(st, k, v)
    db.commit()
    db.refresh(st)
    return st

# ADMIN: agregar social link
@router.post("/social-links", response_model=SocialLinkOut, dependencies=[Depends(require_roles("ADMIN"))])
def add_social_link(payload: SocialLinkIn, db: Session = Depends(get_db)):
    st = _get_or_create_settings(db)
    link = SiteSocialLink(settings_id=st.id, **payload.model_dump())
    db.add(link)
    db.commit()
    db.refresh(link)
    return link

# ADMIN: update social link
@router.patch("/social-links/{link_id}", response_model=SocialLinkOut, dependencies=[Depends(require_roles("ADMIN"))])
def update_social_link(link_id: int, payload: SocialLinkIn, db: Session = Depends(get_db)):
    link = db.get(SiteSocialLink, link_id)
    if not link:
        raise HTTPException(404, "Not found")
    for k, v in payload.model_dump().items():
        setattr(link, k, v)
    db.commit()
    db.refresh(link)
    return link

# ADMIN: delete social link
@router.delete("/social-links/{link_id}", dependencies=[Depends(require_roles("ADMIN"))])
def delete_social_link(link_id: int, db: Session = Depends(get_db)):
    link = db.get(SiteSocialLink, link_id)
    if not link:
        raise HTTPException(404, "Not found")
    db.delete(link)
    db.commit()
    return {"ok": True}

# PUBLIC: settings para la web (sin auth)
@router.get("/public", response_model=SiteSettingsOut)
def public_settings(db: Session = Depends(get_db)):
    st = _get_or_create_settings(db)
    if not st.is_active:
        # si el site está deshabilitado, devuelves 404 o un objeto vacío
        raise HTTPException(404, "Not available")
    # opcional: filtrar links inactivos
    st.social_links = [l for l in st.social_links if l.is_active]
    return st

def _get_or_create_settings(db: Session) -> SiteSettings:
    s = db.query(SiteSettings).first()
    if not s:
        s = SiteSettings(app_name="Spa App")
        db.add(s)
        db.commit()
        db.refresh(s)
    return s

@router.patch("/logo-main", dependencies=[Depends(require_roles("ADMIN", "RECEPTIONIST"))])
def upload_logo_main(file: UploadFile = File(...), db: Session = Depends(get_db)):
    s = _get_or_create_settings(db)

    url = save_image_and_replace(
        file=file,
        old_url=s.logo_main_url,
        folder="site",
        filename_prefix="logo_main",
        make_thumbnail=True,
    )
    s.logo_main_url = url
    db.commit()
    db.refresh(s)
    return {"logo_main_url": s.logo_main_url}

@router.patch("/logo-sidebar", dependencies=[Depends(require_roles("ADMIN", "RECEPTIONIST"))])
def upload_logo_sidebar(file: UploadFile = File(...), db: Session = Depends(get_db)):
    s = _get_or_create_settings(db)

    url = save_image_and_replace(
        file=file,
        old_url=s.logo_sidebar_url,
        folder="site",
        filename_prefix="logo_sidebar",
        make_thumbnail=True,
    )
    s.logo_sidebar_url = url
    db.commit()
    db.refresh(s)
    return {"logo_sidebar_url": s.logo_sidebar_url}

@router.patch("/logo-small", dependencies=[Depends(require_roles("ADMIN", "RECEPTIONIST"))])
def upload_logo_small(file: UploadFile = File(...), db: Session = Depends(get_db)):
    s = _get_or_create_settings(db)

    url = save_image_and_replace(
        file=file,
        old_url=s.logo_small_url,
        folder="site",
        filename_prefix="logo_small",
        make_thumbnail=True,
    )
    s.logo_small_url = url
    db.commit()
    db.refresh(s)
    return {"logo_small_url": s.logo_small_url}