from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_serializer
from app.models.user import Role

class UserCreate(BaseModel):
    email: EmailStr
    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=6, max_length=128)
    position: str = Field(min_length=6, max_length=200)
    phone_e164: str = Field(min_length=10)
    role: str  # "ADMIN" | "RECEPTIONIST" | "EMPLOYEE" | "CUSTOMER"

class UserUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=2, max_length=100)
    last_name: str | None = Field(default=None, min_length=2, max_length=100)
    password: str | None = Field(default=None, min_length=6, max_length=128)
    position: str | None = Field(default=None, min_length=6, max_length=200)
    phone_e164: str | None = Field(default=None, min_length=10)
    is_active: bool | None = None

class UserOut(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    phone_e164: Optional[str] = None
    role: str
    is_active: bool
    image_url: str | None
    sort_order: int | None = None
    position: Optional[str] = None

    model_config = {"from_attributes": True}

    @field_serializer("role")
    def serialize_role(self, v):
        return v.value if isinstance(v, Role) else str(v)

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
