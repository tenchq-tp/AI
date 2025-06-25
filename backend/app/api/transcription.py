from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.db import get_db
from app.schemas.transcription import (
    TranscriptionCreate, TranscriptionUpdate, TranscriptionResponse,
)
from app.crud import crud_transcription

router = APIRouter()


# Transcription

@router.post("/transcriptions/", response_model=TranscriptionResponse)
def create_transcription(transcription: TranscriptionCreate, db: Session = Depends(get_db)):
    return crud_transcription.create_transcription(db, transcription)

@router.get("/transcriptions/{transcription_id}", response_model=TranscriptionResponse)
def read_transcription(transcription_id: UUID, db: Session = Depends(get_db)):
    db_obj = crud_transcription.get_transcription(db, transcription_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Transcription not found")
    return db_obj

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
