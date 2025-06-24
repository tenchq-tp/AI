from sqlalchemy import Column, Text, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.db import Base

class TranscriptionSegment(Base):
    __tablename__ = "transcription_segments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transcription_id = Column(UUID(as_uuid=True), ForeignKey("transcriptions.id", ondelete="CASCADE"))
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    text = Column(Text, nullable=False)

    transcription = relationship("Transcription", back_populates="segments")