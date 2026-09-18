"""Consistent, safe API error handling.

Error responses always use the shape:

    {"error": {"code": "...", "message": "..."}}

Clients never receive stack traces, raw database errors, or API/infrastructure
secrets. Details of unexpected errors are logged server-side only.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("app.core.exceptions")


def error_response(code: str, message: str) -> dict[str, str]:
    return {"error": {"code": code, "message": message}}


class ApiError(Exception):
    """Expected application error that is safe to expose to clients."""

    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class DatabaseUnavailableError(ApiError):
    """Raised when the database cannot be reached for a request."""

    def __init__(self) -> None:
        super().__init__(
            code="DATABASE_UNAVAILABLE",
            message="Database is unavailable.",
            status_code=503,
        )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
        logger.info("ApiError on %s: %s", request.url.path, exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(exc.code, exc.message),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        code = "NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(code, str(exc.detail)),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.warning("Validation error on %s: %s", request.url.path, exc.errors())
        return JSONResponse(
            status_code=422,
            content=error_response("VALIDATION_ERROR", "Request validation failed."),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception("Unhandled exception on %s: %s", request.url.path, exc)
        return JSONResponse(
            status_code=500,
            content=error_response("INTERNAL_ERROR", "Something went wrong."),
        )