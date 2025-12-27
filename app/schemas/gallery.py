from datetime import datetime
from pydantic import BaseModel, Field

class GalleryImageBase(BaseModel):
    title: str | None = Field(default=None, max_length=120)
    caption: str | None = None
    alt_text: str | None = Field(default=None, max_length=200)

    sort_order: int | None = None  # si no viene, lo ponemos automáticamente

class GalleryImageCreate(GalleryImageBase):
    pass

class GalleryImageUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=120)
    caption: str | None = None
    alt_text: str | None = Field(default=None, max_length=200)
    sort_order: int | None = Field(default=None, ge=0)

class GalleryImageOut(GalleryImageBase):
    id: int
    image_url: str | None = None
    thumb_url: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class GalleryReorderItem(BaseModel):
    id: int
    sort_order: int | None = Field(default=None, ge=0)

class GalleryReorderRequest(BaseModel):
    items: list[GalleryReorderItem]
