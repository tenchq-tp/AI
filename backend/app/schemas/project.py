from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime
from app.schemas.audio import AudioFileResponseForProject

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
    audio_file_count: Optional[int] = None
    created_at: Optional[datetime] = None
    last_transcription_updated_at: Optional[datetime] = None
    audio_files: Optional[list[AudioFileResponseForProject]] = []

    class Config:
        from_attributes = True
