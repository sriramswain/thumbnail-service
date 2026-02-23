from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class ThumbnailServiceError(Exception):
    """Base class for domain-specific errors."""


class InvalidImageError(ThumbnailServiceError):
    """Raised when uploaded content is not a valid or supported image."""


class ThumbnailNotFoundError(ThumbnailServiceError):
    """Raised when a thumbnail with the given ID cannot be found."""


class StorageError(ThumbnailServiceError):
    """Raised when storage operations fail."""


def _error_response(
    message: str,
    code: str,
    status_code: int,
    details: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    payload: dict = {
        "error": {
            "code": code,
            "message": message,
        }
    }
    if details:
        payload["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=payload)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(InvalidImageError)
    async def invalid_image_handler(
        request: Request, exc: InvalidImageError
    ) -> JSONResponse:  # pragma: no cover - simple wiring
        return _error_response(
            message=str(exc) or "Invalid image",
            code="INVALID_IMAGE",
            status_code=400,
        )

    @app.exception_handler(ThumbnailNotFoundError)
    async def thumbnail_not_found_handler(
        request: Request, exc: ThumbnailNotFoundError
    ) -> JSONResponse:  # pragma: no cover - simple wiring
        return _error_response(
            message=str(exc) or "Thumbnail not found",
            code="THUMBNAIL_NOT_FOUND",
            status_code=404,
        )

    @app.exception_handler(StorageError)
    async def storage_error_handler(
        request: Request, exc: StorageError
    ) -> JSONResponse:  # pragma: no cover - simple wiring
        return _error_response(
            message=str(exc) or "Storage error",
            code="STORAGE_ERROR",
            status_code=500,
        )

