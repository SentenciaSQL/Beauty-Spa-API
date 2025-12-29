from typing import Optional

from pydantic import BaseModel

class EmployeePublicOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    sort_order: int | None = None
    position: Optional[str] = None

    model_config = {"from_attributes": True}
