from sqlalchemy.orm import Session
from app.models.models import AudioFile
from app.schemas.audio import AudioFileCreate

def create_audio_file(db: Session, audio: AudioFileCreate) -> AudioFile:
    db_audio = AudioFile(**audio.dict())
    db.add(db_audio)
    db.commit()
    db.refresh(db_audio)
    return db_audio
