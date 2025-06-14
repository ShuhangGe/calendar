import uuid
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    timezone: str = "UTC"

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: uuid.UUID
    created_at: datetime
    last_active: datetime
    
    class Config:
        from_attributes = True

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Diary Entry Schemas
class DiaryEntryBase(BaseModel):
    content: str
    date_mentioned: Optional[date] = None
    tags: Dict[str, Any] = {}

class DiaryEntryCreate(DiaryEntryBase):
    pass

class DiaryEntryUpdate(BaseModel):
    content: Optional[str] = None
    date_mentioned: Optional[date] = None
    tags: Optional[Dict[str, Any]] = None

class DiaryEntryResponse(DiaryEntryBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    sync_status: str
    last_modified: datetime
    
    class Config:
        from_attributes = True

# Calendar Event Schemas
class CalendarEventBase(BaseModel):
    title: str
    description: Optional[str] = None
    event_datetime: datetime
    duration_minutes: int = 60
    location: Optional[str] = None
    reminder_minutes: int = 15

class CalendarEventCreate(CalendarEventBase):
    pass

class CalendarEventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    event_datetime: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    location: Optional[str] = None
    reminder_minutes: Optional[int] = None

class CalendarEventResponse(CalendarEventBase):
    id: uuid.UUID
    user_id: uuid.UUID
    sync_status: str
    last_modified: datetime
    
    class Config:
        from_attributes = True

# Conversation Schemas
class ConversationBase(BaseModel):
    user_input: str
    agent_response: str
    classification: str

class ConversationCreate(BaseModel):
    user_input: str

class ConversationResponse(ConversationBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    session_id: uuid.UUID
    
    class Config:
        from_attributes = True

# Chat Schemas
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[uuid.UUID] = None

class ChatResponse(BaseModel):
    response: str
    classification: str
    session_id: uuid.UUID
    timestamp: datetime

# Sync Schemas
class SyncLogResponse(BaseModel):
    id: uuid.UUID
    table_name: str
    record_id: uuid.UUID
    action: str
    sync_timestamp: datetime
    conflict_resolved: bool
    
    class Config:
        from_attributes = True

class SyncStatus(BaseModel):
    pending_syncs: int
    last_sync: Optional[datetime] = None
    conflicts: int

# Pagination Schema
class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int

# Error Schemas
class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None

# UserFact Schemas
class UserFactBase(BaseModel):
    fact_type: str
    fact_key: str
    fact_value: str
    confidence_score: float = 0.0
    is_sensitive: bool = False

class UserFactCreate(UserFactBase):
    source_conversation_id: Optional[uuid.UUID] = None

class UserFactUpdate(BaseModel):
    fact_type: Optional[str] = None
    fact_key: Optional[str] = None
    fact_value: Optional[str] = None
    confidence_score: Optional[float] = None
    is_sensitive: Optional[bool] = None

class UserFactResponse(UserFactBase):
    id: uuid.UUID
    user_id: uuid.UUID
    source_conversation_id: Optional[uuid.UUID] = None
    created_at: datetime
    last_accessed: datetime
    encryption_key_version: int
    
    class Config:
        from_attributes = True

# VectorEmbedding Schemas
class VectorEmbeddingResponse(BaseModel):
    id: uuid.UUID
    fact_id: uuid.UUID
    embedding_model: str
    created_at: datetime
    vector_dimension: int
    
    class Config:
        from_attributes = True

# Fact Search Schemas
class FactSearchRequest(BaseModel):
    query: str
    fact_types: Optional[List[str]] = None
    min_confidence: float = 0.0
    limit: int = 10

class FactSearchResponse(BaseModel):
    facts: List[UserFactResponse]
    relevance_scores: List[float]
    search_time: float

# Fact Extraction Schemas
class FactExtractionRequest(BaseModel):
    conversation_id: uuid.UUID
    force_extraction: bool = False

class FactExtractionResponse(BaseModel):
    extracted_facts: List[UserFactResponse]
    extraction_confidence: float
    processing_time: float 