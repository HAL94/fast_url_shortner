from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.common.app_response import AppResponse
from .api import router
from .core.config import settings
from .core.setup import create_application

import logging
logger = logging.getLogger(__name__)

app = create_application(router=router, settings=settings)


@app.exception_handler(Exception)
async def generic_exception_logger(request: Request, exc: Exception):
    """Logs all unhandled exceptions and returns a proper response."""
    error_msg = exc.__str__()
    # logger.exception(f"An unhandled exception occurred: {error_msg}")
    app_response = AppResponse(success=False, status_code=500, message=(
                f"Failed method {request.method} at URL {request.url}."
                f" Exception message is: {error_msg}."
            ))
    return JSONResponse(content=app_response.__dict__)
