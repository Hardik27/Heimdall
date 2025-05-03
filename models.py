"""
Database models for Tofia Voice Assistant.
Defines SQLAlchemy ORM models for persistent data storage.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import config

Base = declarative_base()

class Caller(Base):
    """Model representing a patient who has called Tofia."""
    __tablename__ = 'callers'
    
    id = Column(Integer, primary_key=True)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=True)
    date_of_birth = Column(String(10), nullable=True)  # Format: YYYY-MM-DD
    insurance_provider = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to call records
    calls = relationship("CallRecord", back_populates="caller")
    
    def __repr__(self):
        return f"<Caller(id={self.id}, phone_number='{self.phone_number}', name='{self.name}')>"


class CallRecord(Base):
    """Model representing a call interaction with Tofia."""
    __tablename__ = 'call_records'
    
    id = Column(Integer, primary_key=True)
    caller_id = Column(Integer, ForeignKey('callers.id'), nullable=False)
    call_type = Column(String(20), nullable=False)  # 'inbound' or 'outbound'
    call_sid = Column(String(50), nullable=True)  # Vapi call identifier
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    summary = Column(Text, nullable=True)
    status = Column(String(20), default="in_progress")  # in_progress, completed, failed
    
    # For appointment calls
    appointment_date = Column(String(10), nullable=True)  # Format: YYYY-MM-DD
    appointment_time = Column(String(8), nullable=True)   # Format: HH:MM AM/PM
    doctor_name = Column(String(100), nullable=True)
    appointment_type = Column(String(100), nullable=True)
    
    # Relationship to caller
    caller = relationship("Caller", back_populates="calls")
    
    def __repr__(self):
        return f"<CallRecord(id={self.id}, call_type='{self.call_type}', status='{self.status}')>"


# Database setup functions
def init_db():
    """Initialize database and create tables if they don't exist."""
    engine = create_engine(config.DATABASE_URL)
    Base.metadata.create_all(engine)
    return engine


def get_session():
    """Create a new database session."""
    engine = create_engine(config.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return Session()
