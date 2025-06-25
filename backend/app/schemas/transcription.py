from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class TranscriptionBase(BaseModel):
    audio_id: UUID
    channel: str  # 'agent' หรือ 'customer'
    start_time: float
    end_time: float
    last_saved_text: Optional[str] = None
    current_text: Optional[str] = None

class TranscriptionCreate(TranscriptionBase):
    pass

class TranscriptionUpdate(BaseModel):
    last_saved_text: Optional[str] = None
    current_text: Optional[str] = None

class TranscriptionResponse(TranscriptionBase):
    id: UUID

    class Config:
        orm_mode = True
