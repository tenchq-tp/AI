from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime

class TranscriptionBase(BaseModel):
    audio_id: UUID
    channel: str  # 'agent' หรือ 'customer'
    start_time: float
    end_time: float
    original_text: Optional[str] = None
    edited_text: Optional[str] = None

class TranscriptionCreate(TranscriptionBase):
    pass

class TranscriptionUpdate(BaseModel):
    edited_text: Optional[str] = None

class TranscriptionResponse(BaseModel):
    id: UUID
    audio_id: UUID
    channel: str  # 'agent' หรือ 'customer'
    start_time: float
    end_time: float
    original_text: Optional[str] = None
    edited_text: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
