import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, UUID, ForeignKey, Integer, Date, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True), server_default=func.now())
    timezone = Column(String, default="UTC")
    
    # Relationships
    diary_entries = relationship("DiaryEntry", back_populates="user")
    calendar_events = relationship("CalendarEvent", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")
    sync_logs = relationship("SyncLog", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"

class DiaryEntry(Base):
    __tablename__ = "diary_entries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    date_mentioned = Column(Date, nullable=True)
    tags = Column(JSON, default=dict)  # For future categorization
    sync_status = Column(String, default="synced")  # synced/pending/conflict
    last_modified = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="diary_entries")
    
    def __repr__(self):
        return f"<DiaryEntry(id={self.id}, user_id={self.user_id})>"

class CalendarEvent(Base):
    __tablename__ = "calendar_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    event_datetime = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, default=60)
    location = Column(String, nullable=True)  # For future location features
    reminder_minutes = Column(Integer, default=15)
    sync_status = Column(String, default="synced")  # synced/pending/conflict
    last_modified = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="calendar_events")
    
    def __repr__(self):
        return f"<CalendarEvent(id={self.id}, title={self.title})>"

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user_input = Column(Text, nullable=False)
    agent_response = Column(Text, nullable=False)
    classification = Column(String, nullable=False)  # diary/calendar/query
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    session_id = Column(UUID(as_uuid=True), default=uuid.uuid4)  # For conversation grouping
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, classification={self.classification})>"

class SyncLog(Base):
    __tablename__ = "sync_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    table_name = Column(String, nullable=False)
    record_id = Column(UUID(as_uuid=True), nullable=False)
    action = Column(String, nullable=False)  # create/update/delete
    sync_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    conflict_resolved = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="sync_logs")
    
    def __repr__(self):
        return f"<SyncLog(id={self.id}, action={self.action})>" 