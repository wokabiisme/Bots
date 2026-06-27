"""Database connection and session management."""

import asyncio
from typing import Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy import event
from loguru import logger
from config.settings import settings
from database.models import Base


class DatabaseManager:
    """Manage database connections and sessions."""
    
    def __init__(
        self,
        database_url: Optional[str] = None,
        pool_size: int = 20,
        max_overflow: int = 40,
        echo: bool = False
    ):
        """Initialize database manager.
        
        Args:
            database_url: Database URL (uses settings if not provided)
            pool_size: Connection pool size
            max_overflow: Maximum overflow connections
            echo: Enable SQL echo
        """
        self.database_url = database_url or settings.database.url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.echo = echo
        
        self.engine = None
        self.async_session_maker = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize database engine and session maker."""
        if self._initialized:
            logger.debug("Database already initialized")
            return
        
        try:
            self.engine = create_async_engine(
                self.database_url,
                echo=self.echo,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_recycle=3600,  # Recycle connections after 1 hour
                pool_pre_ping=True,  # Test connections before using
            )
            
            self.async_session_maker = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False
            )
            
            # Test connection
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info("Database initialized successfully")
            self._initialized = True
        
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def close(self) -> None:
        """Close database engine."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection closed")
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session.
        
        Yields:
            AsyncSession
        """
        if not self._initialized:
            await self.initialize()
        
        async with self.async_session_maker() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                logger.error(f"Session error: {e}")
                raise
            finally:
                await session.close()
    
    async def create_tables(self) -> None:
        """Create all database tables."""
        if not self.engine:
            await self.initialize()
        
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    async def drop_tables(self) -> None:
        """Drop all database tables."""
        if not self.engine:
            await self.initialize()
        
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.info("Database tables dropped")
        except Exception as e:
            logger.error(f"Failed to drop tables: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check database health.
        
        Returns:
            True if database is healthy
        """
        try:
            async with self.engine.connect() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database manager instance
db_manager: Optional[DatabaseManager] = None


async def get_db_manager() -> DatabaseManager:
    """Get global database manager instance.
    
    Returns:
        DatabaseManager instance
    """
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager(
            database_url=settings.database.url,
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow,
            echo=settings.database.echo
        )
        await db_manager.initialize()
    return db_manager
