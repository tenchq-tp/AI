from sqlalchemy import Column, Text, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.db import Base

class AudioFile(Base):
    __tablename__ = "audio_files"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    filename = Column(Text, nullable=False)
    file_path = Column(Text, nullable=False)
    duration_seconds = Column(Float)
    channel_left_path = Column(Text)
    channel_right_path = Column(Text)

    project = relationship("Project", back_populates="audio_files")
    transcriptions = relationship("Transcription", back_populates="audio_file", cascade="all, delete")
