from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.schemas.transcription import TranscriptionResponse

class AudioFileCreate(BaseModel):
    project_id: UUID
    filename: str
    file_path: str
    duration_seconds: Optional[float]
    channel_agent_path: Optional[str]
    channel_customer_path: Optional[str]

class AudioFileResponse(AudioFileCreate):
    id: UUID
    transcriptions: Optional[List[TranscriptionResponse]] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        
# class JustAudioFileResponse(BaseModel):
#     id: UUID
#     project_id: UUID
#     filename: str
#     file_path: str
#     duration_seconds: Optional[float]
#     channel_agent_path: Optional[str]
#     channel_customer_path: Optional[str]
#     created_at: datetime
#     updated_at: Optional[datetime] = None

#     class Config:
#         from_attributes = True
        
class AudioFileResponseForProject(BaseModel):
    id: UUID
    filename: str
    duration_seconds: Optional[float]
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
