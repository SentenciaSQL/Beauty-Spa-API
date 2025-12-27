from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.site_social_link import SocialType

class SocialLinkIn(BaseModel):
    type: SocialType
    url: str = Field(min_length=3, max_length=500)
    label: Optional[str] = Field(default=None, max_length=80)
    sort_order: int = 0
    is_active: bool = True

class SocialLinkOut(SocialLinkIn):
    id: int
    created_at: datetime
    model_config = {"from_attributes": True}

class SiteSettingsUpsert(BaseModel):
    app_name: str = Field(default="Spa App", max_length=120)
    tagline: Optional[str] = Field(default=None, max_length=160)

    logo_main_url: Optional[str] = None
    logo_sidebar_url: Optional[str] = None
    logo_small_url: Optional[str] = None

    whatsapp_phone_e164: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None

    address_text: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    google_maps_iframe: Optional[str] = None

    about_text: Optional[str] = None
    terms_text: Optional[str] = None
    privacy_text: Optional[str] = None

    is_active: bool = True

class SiteSettingsOut(SiteSettingsUpsert):
    id: int
    created_at: datetime
    updated_at: datetime
    social_links: list[SocialLinkOut] = []
    model_config = {"from_attributes": True}
