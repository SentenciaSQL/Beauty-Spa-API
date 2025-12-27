from pydantic import BaseModel

class EmployeeAvailabilitySummaryOut(BaseModel):
    employee_user_id: int
    first_name: str
    last_name: str
    available_count: int
    preview_slots: list[str]

class AvailabilitySummaryOut(BaseModel):
    day: str
    service_id: int
    step_minutes: int
    preview_limit: int
    employees: list[EmployeeAvailabilitySummaryOut]
