

from datetime import datetime
from typing import Optional
from pydantic import AliasGenerator, BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ShortUrlRead(BaseModel):
    id: int
    url: str
    short_code: str
    created_at: datetime
    updated_at: datetime | None
    access_count: int


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