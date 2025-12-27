from pydantic import BaseModel, EmailStr, Field

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class RegisterCustomerIn(BaseModel):
    email: EmailStr
    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=6, max_length=128)
    phone_e164: str = Field(min_length=10)