from datetime import datetime
from pydantic import BaseModel, Field
from app.models.cash import PaymentMethod

class CashEntryCreate(BaseModel):
    amount: float = Field(gt=0)
    method: PaymentMethod = PaymentMethod.CASH
    concept: str | None = None
    appointment_id: int | None = None

class CashEntryOut(BaseModel):
    id: int
    amount: float
    method: PaymentMethod
    concept: str | None
    created_by_user_id: int
    appointment_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}

class CashStatsOut(BaseModel):
    total: float
    by_method: dict[str, float]
    count: int
