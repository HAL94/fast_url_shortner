
from datetime import datetime

import logging
from typing import AsyncGenerator, TypeVar
from sqlalchemy import DateTime, inspect
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError


from app.core.config import AppSettings

T = TypeVar('T', bound='Base')
class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(
        "id", autoincrement=True, nullable=False, unique=True, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now())
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=datetime.now(), onupdate=datetime.now)

    def dict(self):
        """Returns a dict representation of a model."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    @classmethod
    def columns(cls):
        """Returns a set of column names for this model."""
        return {_column.name for _column in inspect(cls).c}

    @classmethod
    def table(cls):
        """Returns the table object for this model."""
        return cls.__table__
    

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
