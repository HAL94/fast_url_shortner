
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import AppSettings


class Base(DeclarativeBase, SerializerMixin):
    pass


settings = AppSettings()

URL = f"postgresql+asyncpg://{settings.PG_USER}:{settings.PG_PW}@{
    settings.PG_SERVER}:{settings.PG_PORT}/{settings.PG_DB}"

logging.log(level=logging.INFO, msg=URL)

engine = create_async_engine(url=URL)


AsyncSessionMaker = async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionMaker() as session:
        try:
            yield session
        except SQLAlchemyError as e:
            # print(f"database error: {e}")
            await session.rollback()
            raise e
        finally:
            await session.close()
