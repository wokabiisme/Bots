"""Database initialization script."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import DatabaseManager
from config.settings import settings
from utils.logger import setup_logger


async def init_database():
    """Initialize database with tables."""
    setup_logger(level="INFO")
    
    db_manager = DatabaseManager(
        database_url=settings.database.url,
        pool_size=settings.database.pool_size,
        max_overflow=settings.database.max_overflow,
        echo=False
    )
    
    try:
        await db_manager.initialize()
        await db_manager.create_tables()
        print("✓ Database initialized successfully")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        sys.exit(1)
    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(init_database())
