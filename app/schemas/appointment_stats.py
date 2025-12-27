from pydantic import BaseModel

class StatusCountOut(BaseModel):
    status: str
    count: int

class ServiceRevenueOut(BaseModel):
    service_id: int
    service_name: str
    count: int
    revenue_estimated: float

class AppointmentStatsOut(BaseModel):
    total: int
    by_status: list[StatusCountOut]
    revenue_estimated: float
    by_service: list[ServiceRevenueOut]
