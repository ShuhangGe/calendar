import uuid
from datetime import datetime, date
from typing import List, Optional
from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from ..models.database import Base, User, DiaryEntry, CalendarEvent, Conversation, SyncLog
from ..config import settings

class StorageService:
    """
    Service class for handling all database operations with user-scoped access
    """
    
    def __init__(self):
        self.engine = create_engine(settings.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def get_db(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    def init_db(self):
        """Initialize database tables"""
        Base.metadata.create_all(bind=self.engine)
    
    # User operations
    def create_user(self, user_data: dict) -> User:
        """Create a new user"""
        db = self.get_db()
        try:
            user = User(**user_data)
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        except SQLAlchemyError as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        db = self.get_db()
        try:
            return db.query(User).filter(User.email == email).first()
        finally:
            db.close()
    
    def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID"""
        db = self.get_db()
        try:
            return db.query(User).filter(User.id == user_id).first()
        finally:
            db.close()
    
    # Diary Entry operations
    def create_diary_entry(self, diary_entry: DiaryEntry) -> DiaryEntry:
        """Create a new diary entry"""
        db = self.get_db()
        try:
            db.add(diary_entry)
            db.commit()
            db.refresh(diary_entry)
            return diary_entry
        except SQLAlchemyError as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def get_diary_entries(self, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[DiaryEntry]:
        """Get paginated diary entries for a user"""
        db = self.get_db()
        try:
            return db.query(DiaryEntry).filter(
                DiaryEntry.user_id == user_id
            ).order_by(DiaryEntry.created_at.desc()).offset(skip).limit(limit).all()
        finally:
            db.close()
    
    def get_recent_diary_entries(self, user_id: uuid.UUID, limit: int = 5) -> List[DiaryEntry]:
        """Get recent diary entries for context"""
        db = self.get_db()
        try:
            return db.query(DiaryEntry).filter(
                DiaryEntry.user_id == user_id
            ).order_by(DiaryEntry.created_at.desc()).limit(limit).all()
        finally:
            db.close()
    
    def search_diary_entries(self, user_id: uuid.UUID, search_term: str) -> List[DiaryEntry]:
        """Search diary entries by content"""
        db = self.get_db()
        try:
            return db.query(DiaryEntry).filter(
                and_(
                    DiaryEntry.user_id == user_id,
                    DiaryEntry.content.ilike(f"%{search_term}%")
                )
            ).order_by(DiaryEntry.created_at.desc()).all()
        finally:
            db.close()
    
    def update_diary_entry(self, user_id: uuid.UUID, entry_id: uuid.UUID, update_data: dict) -> Optional[DiaryEntry]:
        """Update a diary entry"""
        db = self.get_db()
        try:
            entry = db.query(DiaryEntry).filter(
                and_(DiaryEntry.id == entry_id, DiaryEntry.user_id == user_id)
            ).first()
            
            if entry:
                for key, value in update_data.items():
                    if hasattr(entry, key):
                        setattr(entry, key, value)
                entry.last_modified = datetime.now()
                db.commit()
                db.refresh(entry)
            
            return entry
        except SQLAlchemyError as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def delete_diary_entry(self, user_id: uuid.UUID, entry_id: uuid.UUID) -> bool:
        """Delete a diary entry"""
        db = self.get_db()
        try:
            entry = db.query(DiaryEntry).filter(
                and_(DiaryEntry.id == entry_id, DiaryEntry.user_id == user_id)
            ).first()
            
            if entry:
                db.delete(entry)
                db.commit()
                return True
            return False
        except SQLAlchemyError as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    # Calendar Event operations
    def create_calendar_event(self, calendar_event: CalendarEvent) -> CalendarEvent:
        """Create a new calendar event"""
        db = self.get_db()
        try:
            db.add(calendar_event)
            db.commit()
            db.refresh(calendar_event)
            return calendar_event
        except SQLAlchemyError as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def get_calendar_events(self, user_id: uuid.UUID, start_date: date = None, end_date: date = None) -> List[CalendarEvent]:
        """Get calendar events for a user within date range"""
        db = self.get_db()
        try:
            query = db.query(CalendarEvent).filter(CalendarEvent.user_id == user_id)
            
            if start_date:
                query = query.filter(CalendarEvent.event_datetime >= start_date)
            if end_date:
                query = query.filter(CalendarEvent.event_datetime <= end_date)
            
            return query.order_by(CalendarEvent.event_datetime).all()
        finally:
            db.close()
    
    def get_upcoming_events(self, user_id: uuid.UUID, limit: int = 5) -> List[CalendarEvent]:
        """Get upcoming calendar events for context"""
        db = self.get_db()
        try:
            return db.query(CalendarEvent).filter(
                and_(
                    CalendarEvent.user_id == user_id,
                    CalendarEvent.event_datetime >= datetime.now()
                )
            ).order_by(CalendarEvent.event_datetime).limit(limit).all()
        finally:
            db.close()
    
    def search_calendar_events(self, user_id: uuid.UUID, search_term: str) -> List[CalendarEvent]:
        """Search calendar events by title or description"""
        db = self.get_db()
        try:
            return db.query(CalendarEvent).filter(
                and_(
                    CalendarEvent.user_id == user_id,
                    or_(
                        CalendarEvent.title.ilike(f"%{search_term}%"),
                        CalendarEvent.description.ilike(f"%{search_term}%")
                    )
                )
            ).order_by(CalendarEvent.event_datetime).all()
        finally:
            db.close()
    
    def update_calendar_event(self, user_id: uuid.UUID, event_id: uuid.UUID, update_data: dict) -> Optional[CalendarEvent]:
        """Update a calendar event"""
        db = self.get_db()
        try:
            event = db.query(CalendarEvent).filter(
                and_(CalendarEvent.id == event_id, CalendarEvent.user_id == user_id)
            ).first()
            
            if event:
                for key, value in update_data.items():
                    if hasattr(event, key):
                        setattr(event, key, value)
                event.last_modified = datetime.now()
                db.commit()
                db.refresh(event)
            
            return event
        except SQLAlchemyError as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def delete_calendar_event(self, user_id: uuid.UUID, event_id: uuid.UUID) -> bool:
        """Delete a calendar event"""
        db = self.get_db()
        try:
            event = db.query(CalendarEvent).filter(
                and_(CalendarEvent.id == event_id, CalendarEvent.user_id == user_id)
            ).first()
            
            if event:
                db.delete(event)
                db.commit()
                return True
            return False
        except SQLAlchemyError as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    # Conversation operations
    def create_conversation(self, conversation: Conversation) -> Conversation:
        """Create a new conversation record"""
        db = self.get_db()
        try:
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            return conversation
        except SQLAlchemyError as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def get_conversation_history(self, user_id: uuid.UUID, session_id: uuid.UUID = None, limit: int = 50) -> List[Conversation]:
        """Get conversation history for a user"""
        db = self.get_db()
        try:
            query = db.query(Conversation).filter(Conversation.user_id == user_id)
            
            if session_id:
                query = query.filter(Conversation.session_id == session_id)
            
            return query.order_by(Conversation.created_at.desc()).limit(limit).all()
        finally:
            db.close()
    
    def clear_conversation_history(self, user_id: uuid.UUID, session_id: uuid.UUID = None) -> bool:
        """Clear conversation history for a user"""
        db = self.get_db()
        try:
            query = db.query(Conversation).filter(Conversation.user_id == user_id)
            
            if session_id:
                query = query.filter(Conversation.session_id == session_id)
            
            deleted_count = query.delete()
            db.commit()
            return deleted_count > 0
        except SQLAlchemyError as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    # Sync operations (for future offline/online sync)
    def create_sync_log(self, sync_log: SyncLog) -> SyncLog:
        """Create a sync log entry"""
        db = self.get_db()
        try:
            db.add(sync_log)
            db.commit()
            db.refresh(sync_log)
            return sync_log
        except SQLAlchemyError as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def get_pending_syncs(self, user_id: uuid.UUID) -> List[SyncLog]:
        """Get pending sync operations for a user"""
        db = self.get_db()
        try:
            return db.query(SyncLog).filter(
                and_(
                    SyncLog.user_id == user_id,
                    SyncLog.conflict_resolved == False
                )
            ).order_by(SyncLog.sync_timestamp).all()
        finally:
            db.close()
    
    def update_user_last_active(self, user_id: uuid.UUID) -> bool:
        """Update user's last active timestamp"""
        db = self.get_db()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.last_active = datetime.now()
                db.commit()
                return True
            return False
        except SQLAlchemyError as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def update_user(self, user_id: uuid.UUID, update_data: dict) -> Optional[User]:
        """Update user information"""
        db = self.get_db()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                for key, value in update_data.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                db.commit()
                db.refresh(user)
                return user
            return None
        except SQLAlchemyError as e:
            db.rollback()
            raise e
        finally:
            db.close() 