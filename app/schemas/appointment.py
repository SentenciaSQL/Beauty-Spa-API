from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

class AppointmentCreate(BaseModel):
    service_id: int
    employee_user_id: int
    start_at: datetime  # ISO8601
    notes: str | None = None
    step_minutes: int | None = 15

class AppointmentOut(BaseModel):
    id: int
    service_id: int
    customer_user_id: int
    employee_user_id: int
    service_id: int
    start_at: datetime
    end_at: datetime
    status: str
    notes: str | None
    cancel_reason: Optional[str] = None

    model_config = {"from_attributes": True}

class AppointmentReschedule(BaseModel):
    start_at: datetime
    step_minutes: int = 15

class AppointmentCancel(BaseModel):
    reason: Optional[str] = None