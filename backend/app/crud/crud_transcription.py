from sqlalchemy.orm import Session
from uuid import UUID

from app.models.models import Transcription
from app.schemas.transcription import (
    TranscriptionCreate, TranscriptionUpdate,
)

# Transcription
def create_transcription(db: Session, transcription: TranscriptionCreate):
    db_obj = Transcription(**transcription.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_transcription(db: Session, transcription_id: UUID):
    return db.query(Transcription).filter(Transcription.id == transcription_id).first()

def update_transcription(db: Session, transcription_id: UUID, updates: TranscriptionUpdate):
    db_obj = get_transcription(db, transcription_id)
    if not db_obj:
        return None
    for key, value in updates.dict(exclude_unset=True).items():
        setattr(db_obj, key, value)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_transcription(db: Session, transcription_id: UUID):
    obj = get_transcription(db, transcription_id)
    if obj:
        db.delete(obj)
        db.commit()
    return obj

