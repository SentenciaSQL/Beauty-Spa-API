from datetime import datetime
from pydantic import BaseModel

class AppointmentListItemOut(BaseModel):
    id: int
    start_at: datetime
    end_at: datetime
    status: str
    notes: str | None

    service_id: int
    service_name: str

    employee_user_id: int
    employee_first_name: str
    employee_last_name: str

    customer_user_id: int
    customer_first_name: str
    customer_last_name: str
