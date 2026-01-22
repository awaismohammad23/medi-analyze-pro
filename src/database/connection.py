"""
Database connection module for MediAnalyze Pro
Handles database connections and session management
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from .models import Base

# Default database path
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'medanalyze.db')


class DatabaseConnection:
    """Manages database connections and sessions"""
    
    def __init__(self, database_url: str = None):
        """
        Initialize database connection
        
        Args:
            database_url: SQLite database URL (default: uses DEFAULT_DB_PATH)
                         Format: 'sqlite:///path/to/database.db'
        """
        if database_url is None:
            # Use default SQLite database
            db_path = DEFAULT_DB_PATH
            # Ensure directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            database_url = f'sqlite:///{db_path}'
        
        # Create engine with appropriate settings for SQLite
        if database_url.startswith('sqlite'):
            self.engine = create_engine(
                database_url,
                connect_args={'check_same_thread': False},
                poolclass=StaticPool,
                echo=False  # Set to True for SQL query logging
            )
        else:
            # For PostgreSQL/MySQL
            self.engine = create_engine(database_url, echo=False)
        
        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        Base.metadata.drop_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()
    
    def close(self):
        """Close the database connection"""
        self.engine.dispose()


# Global database connection instance
_db_connection = None


def get_db_connection(database_url: str = None) -> DatabaseConnection:
    """
    Get or create the global database connection instance
    
    Args:
        database_url: Optional database URL (only used on first call)
    
    Returns:
        DatabaseConnection instance
    """
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection(database_url)
    return _db_connection


def get_session() -> Session:
    """
    Get a new database session using the global connection
    
    Returns:
        SQLAlchemy Session
    """
    db_conn = get_db_connection()
    return db_conn.get_session()
