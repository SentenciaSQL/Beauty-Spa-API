from pydantic import BaseModel, Field

class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    price: float = Field(ge=0)
    brand: str | None = Field(min_length=2, max_length=150)
    stock: int = Field(ge=0)

class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    price: float | None = Field(default=None, ge=0)
    brand: str | None = Field(min_length=2, max_length=150)
    stock: int | None = Field(default=None, ge=0)
    is_active: bool | None = None

class ProductOut(BaseModel):
    id: int
    name: str
    description: str | None
    price: float
    brand: str | None
    stock: int
    is_active: bool

    model_config = {"from_attributes": True}
