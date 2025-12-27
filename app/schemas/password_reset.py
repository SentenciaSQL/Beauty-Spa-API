from pydantic import BaseModel, EmailStr, Field

class ForgotPasswordIn(BaseModel):
    email: EmailStr

class ResetPasswordIn(BaseModel):
    token: str = Field(min_length=20, max_length=300)
    new_password: str = Field(min_length=6, max_length=128)
