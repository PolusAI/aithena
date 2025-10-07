"""Database manager with lazy initialization.

This module provides a singleton database manager that only initializes
the database connection when it's actually needed, not on import.
"""

from typing import Optional

from polus.aithena.jobs.getopenalex.logger import get_logger
from polus.aithena.jobs.getopenalex.api.database import Database, JobRepository

logger = get_logger(__name__)


class DatabaseManager:
    """Singleton database manager with lazy initialization."""
    
    _instance: Optional["DatabaseManager"] = None
    _db: Optional[Database] = None
    _job_repo: Optional[JobRepository] = None
    _initialized: bool = False
    
    def __new__(cls) -> "DatabaseManager":
        """Ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize(self, database_url: str | None = None) -> None:
        """Initialize the database connection and create tables.
        
        This method is idempotent - calling it multiple times is safe.
        """
        if self._initialized:
            logger.debug("Database already initialized, skipping")
            return
            
        logger.info("Initializing database connection")
        self._db = Database(database_url)
        self._job_repo = JobRepository(self._db)
        
        # Create tables
        try:
            self._db.create_tables()
            logger.info("Database tables created/verified")
        except Exception as e:
            logger.error(f"Error creating database tables: {e!s}")
            # Don't fail completely, some operations might still work
            
        self._initialized = True
        
    @property
    def db(self) -> Database:
        """Get the database instance, initializing if needed."""
        if not self._initialized:
            self.initialize()
        return self._db
    
    @property
    def job_repo(self) -> JobRepository:
        """Get the job repository instance, initializing if needed."""
        if not self._initialized:
            self.initialize()
        return self._job_repo
    
    def is_initialized(self) -> bool:
        """Check if the database has been initialized."""
        return self._initialized
    
    def reset(self) -> None:
        """Reset the database manager (mainly for testing)."""
        self._db = None
        self._job_repo = None
        self._initialized = False


# Global instance
db_manager = DatabaseManager()
