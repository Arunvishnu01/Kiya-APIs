from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class NotFoundException(HTTPException):
    def __init__(self, detail: str = "Resource not found", headers: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail, headers=headers)


class UnauthorizedException(HTTPException):
    def __init__(
        self,
        detail: str = "Could not validate credentials",
        headers: Optional[Dict[str, Any]] = None,
    ):
        if headers is None:
            headers = {"WWW-Authenticate": "Bearer"}
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers=headers,
        )


class ForbiddenException(HTTPException):
    def __init__(self, detail: str = "Not enough permissions", headers: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail, headers=headers)


class ConflictException(HTTPException):
    def __init__(self, detail: str = "Resource already exists", headers: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail, headers=headers)


class BadRequestException(HTTPException):
    def __init__(self, detail: str = "Bad request", headers: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail, headers=headers)
