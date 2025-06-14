import logging
from contextlib import contextmanager
from typing import Generator, Optional
from sqlalchemy import create_engine, pool
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from ..config import settings
from ..models.database import Base

logger = logging.getLogger(__name__)

class DatabaseSessionManager:
    """
    Database session manager with connection pooling and context management
    """
    
    def __init__(self, database_url: str = None):
        """Initialize session manager with connection pooling"""
        self.database_url = database_url or settings.database_url
        
        # Configure engine with connection pooling
        self.engine = create_engine(
            self.database_url,
            poolclass=pool.QueuePool,
            pool_size=10,  # Number of connections to maintain in the pool
            max_overflow=20,  # Additional connections that can be created on demand
            pool_recycle=3600,  # Recycle connections after 1 hour
            pool_pre_ping=True,  # Validate connections before use
            echo=settings.environment == "development"  # Log SQL in development
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # Initialize database tables
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions with automatic cleanup
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    @contextmanager
    def get_transaction(self) -> Generator[Session, None, None]:
        """
        Context manager for database transactions with explicit commit/rollback control
        """
        session = self.SessionLocal()
        try:
            session.begin()
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database transaction error: {e}")
            raise
        finally:
            session.close()
    
    def get_session_sync(self) -> Session:
        """
        Get a database session for synchronous operations
        WARNING: Must be closed manually
        """
        return self.SessionLocal()
    
    def close_session(self, session: Session):
        """Manually close a session"""
        try:
            session.close()
        except Exception as e:
            logger.error(f"Error closing session: {e}")
    
    def health_check(self) -> dict:
        """Check database connectivity and pool status"""
        try:
            with self.get_session() as session:
                # Simple query to test connectivity
                result = session.execute("SELECT 1").scalar()
                
                # Get pool status
                pool_status = {
                    "pool_size": self.engine.pool.size(),
                    "checked_in": self.engine.pool.checkedin(),
                    "checked_out": self.engine.pool.checkedout(),
                    "overflow": self.engine.pool.overflow(),
                    "total_connections": self.engine.pool.size() + self.engine.pool.overflow()
                }
                
                return {
                    "status": "healthy",
                    "connectivity": "ok" if result == 1 else "error",
                    "pool_status": pool_status
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def cleanup(self):
        """Cleanup database connections"""
        try:
            self.engine.dispose()
            logger.info("Database connections cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

# Global session manager instance
session_manager = DatabaseSessionManager()

# Context managers for easy use
@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Global context manager for database sessions
    Usage:
        with get_db_session() as db:
            # Use db session
            pass
    """
    with session_manager.get_session() as session:
        yield session

@contextmanager
def get_db_transaction() -> Generator[Session, None, None]:
    """
    Global context manager for database transactions
    Usage:
        with get_db_transaction() as db:
            # Use db session with transaction
            pass
    """
    with session_manager.get_transaction() as session:
        yield session

# Batch operations utilities
class BatchOperationManager:
    """Manager for batch database operations"""
    
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
    
    @contextmanager
    def batch_insert(self, session: Session):
        """Context manager for batch insert operations"""
        try:
            # Disable autoflush for better performance
            session.autoflush = False
            yield session
            session.flush()
        finally:
            session.autoflush = True
    
    def process_in_batches(self, items: list, process_function, batch_size: int = None):
        """Process items in batches"""
        batch_size = batch_size or self.batch_size
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            try:
                with get_db_transaction() as db:
                    batch_result = process_function(db, batch)
                    results.extend(batch_result)
            except Exception as e:
                logger.error(f"Batch processing error for batch {i//batch_size + 1}: {e}")
                continue
        
        return results

# Utility functions for fact processing
def batch_create_facts(db: Session, facts_data: list) -> list:
    """Batch create facts with optimized performance"""
    from ..models.database import UserFact
    
    try:
        batch_manager = BatchOperationManager()
        with batch_manager.batch_insert(db):
            facts = [UserFact(**fact_data) for fact_data in facts_data]
            db.add_all(facts)
            db.flush()  # Get IDs without committing
            
            return facts
    except Exception as e:
        logger.error(f"Batch fact creation error: {e}")
        raise

def cleanup_old_facts(days_old: int = 365) -> int:
    """Clean up old low-confidence facts"""
    try:
        from datetime import datetime, timedelta
        from ..models.database import UserFact
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        with get_db_transaction() as db:
            # Delete facts older than cutoff with low confidence
            deleted_count = db.query(UserFact).filter(
                UserFact.created_at < cutoff_date,
                UserFact.confidence_score < 0.3
            ).delete()
            
            logger.info(f"Cleaned up {deleted_count} old facts")
            return deleted_count
            
    except Exception as e:
        logger.error(f"Fact cleanup error: {e}")
        return 0 