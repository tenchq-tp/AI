from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from enum import Enum

from app.db.db import get_db
from app.schemas.transcription import (
    TranscriptionUpdate, TranscriptionResponse, 
)
from app.crud import crud_transcription

class ChannelEnum(str, Enum):
    agent = "agent"
    customer = "customer"

router = APIRouter()

@router.get("/transcriptions/{transcription_id}", response_model=TranscriptionResponse)
def read_transcription(transcription_id: UUID, db: Session = Depends(get_db)):
    db_obj = crud_transcription.get_transcription(db, transcription_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Transcription not found")
    return db_obj

@router.get("/transcriptions/by-audio/{audio_id}", response_model=List[TranscriptionResponse])
def read_transcriptions_by_audio_and_channel(
    audio_id: UUID,
    channel: Optional[ChannelEnum] = Query(None),
    db: Session = Depends(get_db)
):
    transcriptions = crud_transcription.get_transcriptions_by_audio_and_channel(db, audio_id, channel)
    if not transcriptions:
        raise HTTPException(status_code=404, detail="No transcriptions found for this audio_id and channel")
    return transcriptions

@router.put("/transcriptions/{transcription_id}", response_model=TranscriptionResponse)
def update_transcription(transcription_id: UUID, updates: TranscriptionUpdate, db: Session = Depends(get_db)):
    db_obj = crud_transcription.update_transcription(db, transcription_id, updates)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Transcription not found")
    return db_obj

@router.delete("/transcriptions/{transcription_id}", response_model=TranscriptionResponse)
def delete_transcription(transcription_id: UUID, db: Session = Depends(get_db)):
    db_obj = crud_transcription.delete_transcription(db, transcription_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Transcription not found")
    return db_obj
