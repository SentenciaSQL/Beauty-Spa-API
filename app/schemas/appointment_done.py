from pydantic import BaseModel
from app.schemas.appointment import AppointmentOut
from app.models.cash import PaymentMethod

class PaymentSuggestion(BaseModel):
    appointment_id: int
    amount: float
    method: PaymentMethod = PaymentMethod.CASH
    concept: str | None = None

class AppointmentDoneOut(BaseModel):
    appointment: AppointmentOut
    payment_suggestion: PaymentSuggestion
