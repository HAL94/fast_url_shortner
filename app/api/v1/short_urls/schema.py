

from datetime import datetime
from re import S
from typing import Optional
from pydantic import AliasGenerator, BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from app.api.v1.short_urls.model import ShortUrl
from app.core.common.mixins import PaginationMixin


class ShortUrlRead(BaseModel):
    id: int
    url: str
    short_code: str
    created_at: datetime
    updated_at: datetime | None
    access_count: int
    model_config = ConfigDict(
        alias_generator=AliasGenerator(to_camel),
        populate_by_name=True,
    )


class ShortUrlCreate(BaseModel):
    url: str
    short_code: str


class ShortUrlUpdate(BaseModel):
    url: str
    access_count: Optional[int] = None


class ShortUrlCreateRequest(BaseModel):
    url: str


class ShortUrlUpsert(BaseModel):
    data: list[ShortUrlCreate]


class ShortUrlCreateResult(BaseModel):
    id: str | int
    url: str
    short_code: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(
        alias_generator=AliasGenerator(to_camel),
        populate_by_name=True,
    )


class ShortUrlUpdateRequest(BaseModel):
    url: str


class ShortUrlUpdateResult(ShortUrlRead):
    pass


class ShortUrlGetResult(ShortUrlRead):
    pass


class ShortUrlDeleteResult(ShortUrlRead):
    pass


class ShortUrlDeleteManyRequest(BaseModel):
    ids: list[int]


class ShortUrlManyPayload(BaseModel):
    id: int
    url: Optional[str] = None
    short_code: Optional[str] = None
    access_count: Optional[int] = None


class ShortUrlUpdateManyRequest(BaseModel):
    records: list[ShortUrlManyPayload]


class ShortUrlUpdateManyResult(BaseModel):
    updated_records: int
    data: list[ShortUrlRead]

    model_config = ConfigDict(
        alias_generator=AliasGenerator(to_camel),
        populate_by_name=True,
    )


PaginatedShortUrl = PaginationMixin.create_pagination_mixin(sortable_fields=ShortUrl.columns(), filterable_fields=ShortUrl.columns())
class ShortUrlGetManyRequest(PaginatedShortUrl):    
    pass


class ShortUrlGetManyResult(BaseModel):
    total_count: int
    data: list[ShortUrlRead]

    model_config = ConfigDict(
        alias_generator=AliasGenerator(to_camel),
        populate_by_name=True
    )
