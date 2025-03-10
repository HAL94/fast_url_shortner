
from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.short_urls.exceptions import ShortUrlDeleteFail, ShortUrlNotFound

from .schema import ShortUrlCreate, ShortUrlCreateResult, ShortUrlRead
from .model import ShortUrl


class URLShortRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_short_url_and_update_access_count(self, short_code: str):
        session = self.session

        short_url = await session.scalar(
            select(ShortUrl).filter(ShortUrl.short_code == short_code)
        )

        if short_url:
            short_url.access_count += 1
            await session.commit()
        else:
            raise ShortUrlNotFound

        await session.close()

        return short_url

    async def get_short_url_stats(self, short_code: str, throw_error=True) -> ShortUrl | None:
        session = self.session

        short_url = await session.scalar(select(ShortUrl).filter(ShortUrl.short_code == short_code))

        if not short_url and throw_error:
            raise ShortUrlNotFound
        elif not short_url and not throw_error:
            return None

        return short_url
    
    async def get_by_url(self, url: str) -> ShortUrl | None:
        session = self.session
        
        short_url = await session.scalar(
            select(ShortUrl).filter(ShortUrl.url == url)
        )
        
        if not short_url:
            raise ShortUrlNotFound
        
        return short_url

    async def create_short_url(self, payload: ShortUrlCreate) -> ShortUrlCreateResult | None:
        session = self.session

        short_url = await session.scalar(
            select(ShortUrl).filter(ShortUrl.short_code == payload.short_code)
        )

        if short_url:
            await session.close()
            return ShortUrlCreateResult.model_validate(short_url.__dict__)

        short_url = ShortUrl(
            url=payload.url, short_code=payload.short_code)

        created_short_url = await session.scalar(
            insert(ShortUrl).values(
                {
                    "url": short_url.url,
                    "short_code": short_url.short_code
                }
            ).returning(ShortUrl)
        )

        await session.commit()

        return ShortUrlCreateResult.model_validate(created_short_url.__dict__)

    async def update_short_url(self, short_code: str, new_url: str) -> ShortUrl:
        session = self.session

        updated_short_url = await session.scalar(
            update(ShortUrl).values(url=new_url).where(
                ShortUrl.short_code == short_code).returning(ShortUrl)
        )

        if updated_short_url is None:
            raise ShortUrlNotFound

        await session.commit()

        return updated_short_url

    async def delete_short_url(self, short_code: str) -> ShortUrl:
        session = self.session

        short_url = await session.scalar(
            delete(ShortUrl).where(ShortUrl.short_code == short_code).returning(ShortUrl)
        )

        await session.commit()

        if not short_url:
            raise ShortUrlNotFound

        return short_url

    async def upsert_bulk_urls(self, payload: list[ShortUrlCreate]) -> list[ShortUrlRead]:
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        
        session = self.session

        stmt = pg_insert(ShortUrl).values(
            [{"url": item.url, "short_code": item.short_code}
                for item in payload]
        )

        # essentially makes an insert also an upsert (dialect specific)
        stmt = stmt.on_conflict_do_update(
            index_elements=[ShortUrl.url], set_=dict(                
                short_code=stmt.excluded.short_code,
                updated_at=func.now()
            )
        )

        short_urls_scalars = await session.scalars(
            stmt.returning(ShortUrl), execution_options={"populate_existing": True}
        )

        await session.commit()

        created_short_urls = short_urls_scalars.all()
        
        return created_short_urls
