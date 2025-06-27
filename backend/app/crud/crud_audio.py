from sqlalchemy.orm import Session, joinedload
from app.models.models import AudioFile
from app.schemas.audio import AudioFileCreate
from uuid import UUID

def get_audio_file(db: Session, audio_id: UUID):
    return db.query(AudioFile).options(joinedload(AudioFile.transcriptions)).filter(AudioFile.id == audio_id).first()

def get_audio_files(db: Session, skip: int = 0, limit: int = 100):
    return db.query(AudioFile).offset(skip).limit(limit).all()

def create_audio_file(db: Session, audio: AudioFileCreate) -> AudioFile:
    db_audio = AudioFile(**audio.dict())
    db.add(db_audio)
    db.commit()
    db.refresh(db_audio)
    return db_audio

def delete_audio_file(db: Session, audio_id: int):
    db.query(AudioFile).filter(AudioFile.id == audio_id).delete()
    db.commit()
