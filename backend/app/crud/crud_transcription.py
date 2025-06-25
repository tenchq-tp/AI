from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

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

def get_transcriptions_by_audio_and_channel(db: Session, audio_id: UUID, channel: Optional[str]):
    query = db.query(Transcription).filter(Transcription.audio_id == audio_id)
    if channel:
        query = query.filter(Transcription.channel == channel)
    return query.order_by(Transcription.start_time).all()

def update_transcription(db: Session, transcription_id: UUID, updates: TranscriptionUpdate):
    db_obj = get_transcription(db, transcription_id)
    if not db_obj:
        return None

    update_data = updates.dict(exclude_unset=True)

    if "edited_text" in update_data:
        if db_obj.edited_text is not None:
            db_obj.original_text = db_obj.edited_text
        db_obj.edited_text = update_data["edited_text"]

    for key, value in update_data.items():
        if key != "edited_text":  # ข้าม edited_text 
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

