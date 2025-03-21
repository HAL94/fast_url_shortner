from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, RedirectResponse

from typing import Optional

from app.core.common.app_response import AppResponse
from app.core.exceptions import NotFoundException, ServerFailException
from app.core.config import AppSettings

from .exceptions import ShortUrlDeleteFail, ShortUrlNotFound
from .schema import ShortUrlCreateRequest, ShortUrlCreateResult, ShortUrlGetResult, ShortUrlRead, ShortUrlUpdateRequest, ShortUrlUpdateResult
from .service import URLShortenerService

settings = AppSettings()

router = APIRouter(tags=["shorten"], prefix='/shorten')


@router.post('/')
async def shorten_url(
    payload: ShortUrlCreateRequest,
    url_short_service: URLShortenerService = Depends(URLShortenerService),
):
    created_short_url = await url_short_service.create_short_url(payload)
    app_response_data = AppResponse(data=created_short_url, status_code=201)
    encoded_app_response_data = jsonable_encoder(app_response_data)
    return JSONResponse(content=encoded_app_response_data, status_code=201)


@router.post('/bulk-upsert', response_model=AppResponse[list[ShortUrlCreateResult]])
async def upsert_many(
    payload: list[ShortUrlCreateRequest],
    url_short_service: URLShortenerService = Depends(URLShortenerService),
):
    created_short_urls = await url_short_service.upsert_short_urls(payload)
    return AppResponse(data=created_short_urls, status_code=200)


@router.get('/{short_code}')
async def get_url_by_code(short_code: str, url_short_service: URLShortenerService = Depends(URLShortenerService)):
    try:
        short_url = await url_short_service.get_short_url(short_code)
        if not short_url:
            raise NotFoundException
        return AppResponse(data=short_url)
    except NotFoundException as e:
        raise NotFoundException(detail="Short Url not found") from e


@router.get('/{short_code}/stats', response_model=AppResponse[ShortUrlGetResult])
async def get_url_by_code(short_code: str, url_short_service: URLShortenerService = Depends(URLShortenerService)):
    try:
        short_url = await url_short_service.get_short_url_stats(short_code)
        return AppResponse(data=short_url, status_code=200)
    except ShortUrlNotFound:
        raise NotFoundException(detail="Short Url not found")


@router.put('/{short_code}', response_model=AppResponse[ShortUrlUpdateResult])
async def update_url(short_code: str, short_url_update: ShortUrlUpdateRequest, url_short_service: URLShortenerService = Depends(URLShortenerService)):
    try:
        updated_short_url = await url_short_service.update_short_url(short_code=short_code, new_url=short_url_update.url)
        return AppResponse(data=updated_short_url, status_code=200)
    except ShortUrlNotFound:
        raise NotFoundException(detail="Short Url not found")


@router.delete('/{short_code}')
async def delete_url(short_code: str, url_short_service: URLShortenerService = Depends(URLShortenerService)):
    try:
        deleted_short_url = await url_short_service.delete_short_url(short_code)
        return AppResponse(data=deleted_short_url, status_code=200, message="Successfully deleted")
    except ShortUrlNotFound:
        raise NotFoundException(detail="Short Url not found")
    except ShortUrlDeleteFail:
        raise ServerFailException(detail="Failed to delete url")
