from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from src.config import _Config
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DATABASE_URL = _Config.DATABASE_URL
engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@asynccontextmanager
async def get_db() -> AsyncSession:
    """Контекстный менеджер для работы с БД"""
    session = SessionLocal()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        await session.close()