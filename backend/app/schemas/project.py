from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(ProjectBase):
    pass

class ProjectResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None

    class Config:
        orm_mode = True
