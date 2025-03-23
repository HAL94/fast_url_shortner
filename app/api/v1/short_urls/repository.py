
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import Depends
from app.api.v1.short_urls.exceptions import ShortUrlNotFound
from app.api.v1.short_urls.schema import ShortUrlRead
from app.core.db.base_repo import BaseRepo
from app.core.db.database import get_async_session

from .model import ShortUrl


def get_short_url_repo(db: AsyncSession = Depends(get_async_session())):
    return URLShortRepository(session=db)


class URLShortRepository(BaseRepo[ShortUrl, ShortUrlRead]):
    __dbmodel__ = ShortUrl
    __model__ = ShortUrlRead

    async def get_by_short_code(self, short_code: str) -> ShortUrlRead | None:
        try:
            found_short_url = await super().get_one(val=short_code, field='short_code')
            return found_short_url
        except ShortUrlNotFound:
            return None
        except Exception as e:
            return None
