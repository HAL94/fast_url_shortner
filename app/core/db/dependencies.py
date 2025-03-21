from typing import Type, TypeVar
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_async_session

T = TypeVar('T')

def get_repository(Repo:Type [T], **kwargs) -> T:
    def get_repo(db: AsyncSession = Depends(get_async_session)):
        return Repo(db, **kwargs)
    return Depends(get_repo)
