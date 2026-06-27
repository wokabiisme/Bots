"""Repository pattern for data access."""

from typing import List, Optional, Any, Generic, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from loguru import logger

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """Base repository for database operations."""
    
    def __init__(self, session: AsyncSession, model: type):
        """Initialize repository.
        
        Args:
            session: Async database session
            model: SQLAlchemy model class
        """
        self.session = session
        self.model = model
    
    async def create(self, **kwargs) -> T:
        """Create new record.
        
        Args:
            **kwargs: Model attributes
            
        Returns:
            Created model instance
        """
        try:
            instance = self.model(**kwargs)
            self.session.add(instance)
            await self.session.flush()
            return instance
        except Exception as e:
            logger.error(f"Error creating {self.model.__name__}: {e}")
            raise
    
    async def get(self, id: Any) -> Optional[T]:
        """Get record by ID.
        
        Args:
            id: Record ID
            
        Returns:
            Model instance or None
        """
        try:
            stmt = select(self.model).where(self.model.id == id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__}: {e}")
            return None
    
    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[T]:
        """Get all records with pagination.
        
        Args:
            limit: Maximum records to return
            offset: Offset for pagination
            
        Returns:
            List of model instances
        """
        try:
            stmt = select(self.model).limit(limit).offset(offset)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting all {self.model.__name__}: {e}")
            return []
    
    async def update(self, id: Any, **kwargs) -> Optional[T]:
        """Update record.
        
        Args:
            id: Record ID
            **kwargs: Attributes to update
            
        Returns:
            Updated model instance or None
        """
        try:
            instance = await self.get(id)
            if not instance:
                return None
            
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            
            await self.session.flush()
            return instance
        except Exception as e:
            logger.error(f"Error updating {self.model.__name__}: {e}")
            raise
    
    async def delete(self, id: Any) -> bool:
        """Delete record.
        
        Args:
            id: Record ID
            
        Returns:
            True if deleted successfully
        """
        try:
            instance = await self.get(id)
            if not instance:
                return False
            
            await self.session.delete(instance)
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error deleting {self.model.__name__}: {e}")
            raise
    
    async def filter(
        self,
        limit: int = 100,
        offset: int = 0,
        **filters
    ) -> List[T]:
        """Filter records by attributes.
        
        Args:
            limit: Maximum records to return
            offset: Offset for pagination
            **filters: Filter conditions
            
        Returns:
            List of filtered model instances
        """
        try:
            conditions = []
            for key, value in filters.items():
                if hasattr(self.model, key):
                    conditions.append(getattr(self.model, key) == value)
            
            stmt = select(self.model)
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            stmt = stmt.limit(limit).offset(offset)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error filtering {self.model.__name__}: {e}")
            return []
    
    async def count(self) -> int:
        """Count total records.
        
        Returns:
            Total number of records
        """
        try:
            stmt = select(self.model)
            result = await self.session.execute(stmt)
            return len(result.scalars().all())
        except Exception as e:
            logger.error(f"Error counting {self.model.__name__}: {e}")
            return 0
    
    async def exists(self, **filters) -> bool:
        """Check if record exists.
        
        Args:
            **filters: Filter conditions
            
        Returns:
            True if record exists
        """
        try:
            records = await self.filter(limit=1, **filters)
            return len(records) > 0
        except Exception as e:
            logger.error(f"Error checking existence in {self.model.__name__}: {e}")
            return False
