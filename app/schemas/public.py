from pydantic import BaseModel

class EmployeePublicOut(BaseModel):
    id: int
    first_name: str
    last_name: str

    model_config = {"from_attributes": True}
