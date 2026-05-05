from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from collections.abc import AsyncGenerator

from core.config import settings

from models.base import Base 

# Engine 
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG, # SQL logging only in debug mode
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True, # Drops stale connections before use
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False, # Keeps ORM objects usable after commit
    autocommit=False,
    autoflush=False,
)

# # Base model 
# class Base(DeclarativeBase):
#     """All SQLAlchemy ORM models inherit from this."""
#     pass


# FastAPI dependency 
async def get_db() -> AsyncGenerator [AsyncSession, None]:  
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()