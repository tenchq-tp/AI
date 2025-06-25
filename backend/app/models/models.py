from sqlalchemy import Column, Text, ForeignKey, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.db.db import Base

class Project(Base):
    __tablename__ = "projects"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    description = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    audio_files = relationship("AudioFile", back_populates="project", cascade="all, delete")

class AudioFile(Base):
    __tablename__ = "audio_files"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    filename = Column(Text, nullable=False)
    file_path = Column(Text, nullable=False)
    duration_seconds = Column(Float)
    channel_agent_path = Column(Text)
    channel_customer_path = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="audio_files")
    transcriptions = relationship("Transcription", back_populates="audio_file", cascade="all, delete")
    
class Transcription(Base):
    __tablename__ = "transcriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audio_id = Column(UUID(as_uuid=True), ForeignKey("audio_files.id", ondelete="CASCADE"))
    channel = Column(Text, nullable=False)  # 'agent' or 'customer'

    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    
    original_text = Column(Text)
    edited_text = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    audio_file = relationship("AudioFile", back_populates="transcriptions")
