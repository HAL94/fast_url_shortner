
import string
import random

from app.api.v1.short_urls.model import ShortUrl
from app.api.v1.short_urls.schema import ShortUrlCreate, ShortUrlCreateRequest, ShortUrlCreateResult, ShortUrlDeleteResult, ShortUrlGetResult, ShortUrlUpdateResult
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
            if not await self.url_short_repo.get_short_url_stats(code, throw_error=False):
                return code

    async def create_short_url(self, payload: ShortUrlCreateRequest) -> ShortUrlCreateResult:
        short_url_found = await self.url_short_repo.get_by_url(payload.url)
        
        if isinstance(short_url_found, ShortUrl):
            return ShortUrlCreateResult.model_validate(short_url_found.__dict__)
        
        short_code = await self._generate_short_code()
        
        return await self.url_short_repo.create_short_url(ShortUrlCreate(url=payload.url, short_code=short_code))

    async def get_short_url(self, short_code: str) -> ShortUrlGetResult | None:
        return await self.url_short_repo.get_short_url_and_update_access_count(short_code)

    async def get_short_url_stats(self, short_code: str) -> ShortUrlGetResult | None:
        return await self.url_short_repo.get_short_url_stats(short_code)

    async def update_short_url(self, short_code: str, new_url: str) -> ShortUrlUpdateResult | None:
        updated_short_url = await self.url_short_repo.update_short_url(short_code, new_url)

        return ShortUrlUpdateResult.model_validate(updated_short_url.__dict__)

    async def delete_short_url(self, short_code: str) -> ShortUrlDeleteResult | None:
        deleted_short_url = await self.url_short_repo.delete_short_url(short_code=short_code)
        return ShortUrlDeleteResult.model_validate(deleted_short_url.__dict__)
    
    async def upsert_short_urls(self, payload: list[ShortUrlCreateRequest]) -> list[ShortUrlCreateResult]:
        transformed_payload = [ShortUrlCreate(url=item.url, short_code=await self._generate_short_code()) for item in payload]
        
        return await self.url_short_repo.upsert_bulk_urls(transformed_payload)
