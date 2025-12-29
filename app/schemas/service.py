from pydantic import BaseModel, Field

class ServiceCreate(BaseModel):
    name: str
    description: str | None = None
    duration_minutes: int = Field(ge=5, le=600)
    price: float = Field(ge=0)

class ServiceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    duration_minutes: int | None = Field(default=None, ge=5, le=600)
    price: float | None = Field(default=None, ge=0)
    is_active: bool | None = None

class ServiceOut(BaseModel):
    id: int
    name: str
    description: str | None
    duration_minutes: int
    price: float
    is_active: bool
    image_url: str | None
    sort_order: int | None = Field(default=None, ge=0)
    is_popular: bool | None = None
    is_deal: bool | None = None

    model_config = {"from_attributes": True}