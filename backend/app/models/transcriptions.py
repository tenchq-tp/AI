from sqlalchemy import Column, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.db import Base

class Transcription(Base):
    __tablename__ = "transcriptions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audio_id = Column(UUID(as_uuid=True), ForeignKey("audio_files.id", ondelete="CASCADE"))
    channel = Column(Text, nullable=False)  # 'L' or 'R'
    speaker_label = Column(Text)
    text = Column(Text)

    audio_file = relationship("AudioFile", back_populates="transcriptions")
    segments = relationship("TranscriptionSegment", back_populates="transcription", cascade="all, delete")
