
import string
import random

from app.api.v1.short_urls.model import ShortUrl
from app.api.v1.short_urls.schema import ShortUrlCreate, ShortUrlCreateRequest, ShortUrlCreateResult, ShortUrlDeleteManyRequest, ShortUrlDeleteResult, ShortUrlGetResult, ShortUrlRead, ShortUrlUpdate, ShortUrlUpdateManyRequest, ShortUrlUpdateManyResult, ShortUrlUpdateResult
from app.core.db.dependencies import get_repository

from .repository import URLShortRepository


class URLShortenerService:
    def __init__(self, code_length=6, url_short_repo: URLShortRepository = get_repository(URLShortRepository)):
        self.code_length = code_length
        self.url_short_repo = url_short_repo

    async def _generate_short_code(self) -> str:
        characters = string.ascii_letters + string.digits
        while True:

            code = ''.join(random.choices(characters, k=self.code_length))
            if not await self.url_short_repo.get_by_short_code(short_code=code):
                return code

    async def create_short_url(self, payload: ShortUrlCreateRequest) -> ShortUrlCreateResult:
        short_code = await self._generate_short_code()

        return await self.url_short_repo.create(data=ShortUrlCreate(url=payload.url, short_code=short_code), return_model=ShortUrlCreateResult)

    async def get_short_url(self, short_code: str, update_stats = False) -> ShortUrlGetResult | None:
        short_url: ShortUrlGetResult = await self.url_short_repo.get_by_short_code(short_code=short_code)
        
        if not update_stats:
            return short_url
        
        short_url.access_count += 1

        return await self.url_short_repo.update_one(data=short_url,
                                                    where_clause=[ShortUrl.short_code == short_code])

    async def update_short_url(self, short_code: str, new_url: str) -> ShortUrlUpdateResult | None:
        data = ShortUrlUpdate(url=new_url)
        return await self.url_short_repo.update_one(data=data, return_model=ShortUrlUpdateResult, where_clause=[ShortUrl.short_code == short_code])

    async def delete_short_url(self, short_code: str) -> ShortUrlDeleteResult | None:
        return await self.url_short_repo.delete_one(val=short_code, field='short_code', return_model=ShortUrlDeleteResult)

    async def upsert_short_urls(self, payload: list[ShortUrlCreateRequest]) -> list[ShortUrlCreateResult]:
        transformed_payload = [ShortUrlCreate(url=item.url, short_code=await self._generate_short_code()) for item in payload]
        # index_elements=[ShortUrl.url],
        return await self.url_short_repo.upsert_many(data=transformed_payload, index_elements=[ShortUrl.url], return_model=ShortUrlCreateResult)
    
    async def delete_many(self, payload: ShortUrlDeleteManyRequest):
        return await self.url_short_repo.delete_many(where_clause=[ShortUrl.id.in_(payload.ids)])
    
    async def update_many(self, payload: ShortUrlUpdateManyRequest) -> ShortUrlUpdateManyResult:         
        data = await self.url_short_repo.update_many(data=payload.records)
        updated_records = len(data)
        return ShortUrlUpdateManyResult(updated_records=updated_records, data=data)