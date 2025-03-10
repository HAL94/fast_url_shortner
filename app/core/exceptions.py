from typing import Any
from fastapi import HTTPException, status

from app.core.common.app_response import AppResponse


class NotFoundException(HTTPException):
    """Base exception for resource not found errors."""

    def __init__(self, detail: Any = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=AppResponse(
            success=False, status_code=404, message=detail).__dict__)


class AlreadyExistsException(HTTPException):
    """Base exception for resource already exists errors."""

    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=AppResponse(
            success=False, status_code=409, message=detail).__dict__)


class UnauthorizedException(HTTPException):
    """Base exception for unauthorized access errors."""

    def __init__(self, detail: str = "Unauthorized access"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=AppResponse(
            success=False, status_code=401, message=detail).__dict__)


class ForbiddenException(HTTPException):
    """Base exception for forbidden access errors."""

    def __init__(self, detail: str = "Access forbidden"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=AppResponse(
            success=False, status_code=409, message=detail).__dict__)


class ServerFailException(HTTPException):
    def __init__(self, detail: str = "An error occured"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                         detail=AppResponse(success=False, status_code=500, message=detail).__dict__)
