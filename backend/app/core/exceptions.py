from fastapi import Request, status
from fastapi.responses import JSONResponse
from loguru import logger

class APIException(Exception):
    """Base exception for API errors."""
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail

class AppError(APIException):
    """Legacy AppError support, mapping to APIException."""
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=message)

async def api_exception_handler(request: Request, exc: APIException):
    """Handles all APIException instances."""
    logger.error(f"API Error [{exc.status_code}] on {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "path": request.url.path,
            "status": "error"
        },
    )

async def unhandled_exception_handler(request: Request, exc: Exception):
    """Fallback for any unhandled exceptions."""
    logger.exception(f"Unhandled Exception on {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected internal server error occurred.",
            "status": "error"
        },
    )
