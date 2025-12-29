from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl

class SlideBase(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    subtitle: str | None = Field(default=None, max_length=200)
    secondary_title: str | None = Field(default=None, max_length=120)
    link_url: str | None = Field(default=None, max_length=500)
    alt_text: str | None = Field(default=None, max_length=200)

    sort_order: int | None = None
    is_active: bool = True

    starts_at: datetime | None = None
    ends_at: datetime | None = None

class SlideCreate(SlideBase):
    pass

class SlideUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=120)
    subtitle: str | None = Field(default=None, max_length=200)
    secondary_title: str | None = Field(default=None, max_length=120)
    link_url: str | None = Field(default=None, max_length=500)
    alt_text: str | None = Field(default=None, max_length=200)

    sort_order: int | None = None
    is_active: bool | None = None

    starts_at: datetime | None = None
    ends_at: datetime | None = None

class SlideOut(SlideBase):
    id: int
    image_url: str | None = None
    thumb_url: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class SlideReorderItem(BaseModel):
    id: int
    sort_order: int | None = Field(default=None, ge=0)

class SlideReorderRequest(BaseModel):
    items: list[SlideReorderItem]
