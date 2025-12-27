from pydantic import BaseModel

class EmployeeSlotsOut(BaseModel):
    employee_user_id: int
    first_name: str
    last_name: str
    slots: list[str]  # ISO datetimes

class AvailabilityByServiceOut(BaseModel):
    day: str
    service_id: int
    step_minutes: int
    employees: list[EmployeeSlotsOut]
