from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.deps import get_current_user
from app.crud.availability import get_employee_availability

router = APIRouter(prefix="/availability")

@router.get("/employees/{employee_user_id}")
def availability_for_employee(
    employee_user_id: int,
    day: date = Query(..., description="YYYY-MM-DD"),
    service_id: int = Query(...),
    step_minutes: int = Query(15, ge=5, le=60),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),  # público más adelante si quieres, por ahora protegido
):
    try:
        slots = get_employee_availability(db, employee_user_id, day, service_id, step_minutes)
        return {"employee_user_id": employee_user_id, "day": str(day), "service_id": service_id, "slots": slots}
    except ValueError as e:
        raise HTTPException(400, str(e))
