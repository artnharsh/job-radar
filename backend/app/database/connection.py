"""
Async SQLAlchemy engine + session factory.

- AsyncEngine is created once at module level.
- get_db() is the FastAPI dependency injected into every route
  that needs a database session.
- Sessions are scoped to a single request — committed on success,
  rolled back on exception, always closed.
"""

from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.utils.config import settings
from app.utils.logger import get_logger

log = get_logger(__name__)

# NullPool is intentional for async: each coroutine manages its own
# connection from the underlying asyncpg pool.
engine = create_async_engine(
    settings.database_url,
    echo=not settings.is_production,  # SQL logging in dev only
    future=True,
    pool_pre_ping=True,
    poolclass=NullPool,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency.
    Usage:
        db: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()