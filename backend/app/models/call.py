from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.config.database import Base


class Call(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), index=True)
    vapi_call_id = Column(String, unique=True, index=True, nullable=True)
    room_name = Column(String, unique=True, index=True, nullable=True)
    status = Column(String, default="started")
    ended_reason = Column(String, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    recording_url = Column(String, nullable=True)
    transcript = Column(Text, nullable=True)
    extracted_data = Column(JSON, nullable=True)
    cost = Column(Float, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    lead = relationship("Lead", back_populates="calls")
