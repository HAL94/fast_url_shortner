from fastapi import APIRouter

from .short_urls.route import router as shorturls_router

router = APIRouter(prefix="/v1")

router.include_router(shorturls_router)