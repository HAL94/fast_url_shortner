
from datetime import datetime
import logging
from typing import Any, AsyncGenerator, Type
from sqlalchemy import DateTime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError
# from sqlalchemy.ext.declarative import declarative_base

from app.core.config import AppSettings
# from app.core.db.mixins import IdMixin, TimestampMixin


class Base(DeclarativeBase):    
    id: Mapped[int] = mapped_column("id", autoincrement=True, nullable=False, unique=True, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=datetime.now())
 
    def dict(self):
        """Returns a dict representation of a model."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# class CustomBase(object):
    # id: Mapped[int] = mapped_column("id", autoincrement=True, nullable=False, unique=True, primary_key=True)
    # created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now())
    # updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=datetime.now())
    
#     def dict(self):
#         """Returns a dict representation of a model."""
#         return {c.name: getattr(self, c.name) for c in self.__table__.columns}




# Base: Type[CustomBase] = declarative_base(cls=CustomBase)

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
