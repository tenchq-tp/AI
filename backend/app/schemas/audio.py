from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class TranscriptionResponse(BaseModel):
    id: UUID
    audio_id: UUID
    channel: str
    start_time: float
    end_time: float
    last_saved_text: Optional[str] = None
    current_text: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

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

    class Config:
        orm_mode = True
