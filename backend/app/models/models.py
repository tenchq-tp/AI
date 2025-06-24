from sqlalchemy import Column, Text, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.db import Base

class Project(Base):
    __tablename__ = "projects"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    description = Column(Text)

    audio_files = relationship("AudioFile", back_populates="project", cascade="all, delete")

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
    
class Transcription(Base):
    __tablename__ = "transcriptions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audio_id = Column(UUID(as_uuid=True), ForeignKey("audio_files.id", ondelete="CASCADE"))
    channel = Column(Text, nullable=False)  # 'L' or 'R'
    speaker_label = Column(Text)
    text = Column(Text)

    audio_file = relationship("AudioFile", back_populates="transcriptions")
    segments = relationship("TranscriptionSegment", back_populates="transcription", cascade="all, delete")
    
class TranscriptionSegment(Base):
    __tablename__ = "transcription_segments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transcription_id = Column(UUID(as_uuid=True), ForeignKey("transcriptions.id", ondelete="CASCADE"))
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    text = Column(Text, nullable=False)

    transcription = relationship("Transcription", back_populates="segments")