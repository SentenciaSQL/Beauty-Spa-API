from datetime import date, datetime
from pydantic import BaseModel, Field

class TestimonialBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    message: str = Field(min_length=5, max_length=1000)

    testimonial_date: date

    rating: int | None = Field(default=None, ge=1, le=5)
    sort_order: int | None = None  # si no viene, lo ponemos automático

class TestimonialCreate(TestimonialBase):
    pass

class TestimonialUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    message: str | None = Field(default=None, min_length=5, max_length=1000)
    testimonial_date: date | None = None
    rating: int | None = Field(default=None, ge=1, le=5)
    sort_order: int | None = Field(default=None, ge=0)

class TestimonialOut(TestimonialBase):
    id: int
    image_url: str | None = None
    thumb_url: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class TestimonialReorderItem(BaseModel):
    id: int
    sort_order: int | None = Field(default=None, ge=0)

class TestimonialReorderRequest(BaseModel):
    items: list[TestimonialReorderItem]
