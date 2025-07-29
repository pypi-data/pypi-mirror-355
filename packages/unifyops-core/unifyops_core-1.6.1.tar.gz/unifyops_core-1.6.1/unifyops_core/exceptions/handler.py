# unifyops_core/exceptions/handlers.py

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from typing import Callable

from .base import AppException
from .models import ErrorResponse
from unifyops_core.logging import get_logger

logger = get_logger(__name__)

def register_exception_handlers(app: FastAPI) -> None:
    """
    Wire up global exception handlers on the given FastAPI app
    for AppException subclasses and any uncaught Exception.
    """

    @app.exception_handler(AppException)
    async def _handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
        """
        Catch any AppException (or subclass), convert it via .to_response(),
        and return a JSONResponse with the correct status code and body.
        """
        # exc.to_response() returns a Pydantic ErrorResponse
        payload: ErrorResponse = exc.to_response()
        return JSONResponse(
            status_code=payload.status_code,
            content=payload.dict(exclude_none=True),
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
        """
        Catch-all for any other Exception, log it, and return a generic
        500 error in the same format.
        """
        logger.exception("Unhandled exception during request %s %s", request.method, request.url)
        generic = AppException("Internal server error")
        payload: ErrorResponse = generic.to_response()
        return JSONResponse(
            status_code=generic.status_code,
            content=payload.dict(exclude_none=True),
        )
