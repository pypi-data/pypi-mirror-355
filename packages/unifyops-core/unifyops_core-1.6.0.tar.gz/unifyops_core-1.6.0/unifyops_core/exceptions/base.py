from typing import Any, Dict, List, Optional
import traceback, sys
from http import HTTPStatus
from uuid import uuid4

from .models import ErrorResponse, ErrorDetail

class AppException(Exception):
    """Base for all application exceptions."""
    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR
    error_type: str = "server_error"

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        error_type: Optional[str] = None,
        details: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        if error_type is not None:
            self.error_type = error_type
        self.error_id = str(uuid4())
        self.details = [
            ErrorDetail(**d) if not isinstance(d, ErrorDetail) else d
            for d in (details or [])
        ]
        # Capture traceback at the raise point (if desired)
        tb = sys.exc_info()[2]
        self.trace = traceback.format_tb(tb) if tb else None

    def to_response(self) -> ErrorResponse:
        return ErrorResponse(
            status_code=self.status_code,
            message=self.message,
            details=self.details or None,
            error_id=self.error_id,
            error_type=self.error_type,
        )

class ClientError(AppException):
    status_code = HTTPStatus.BAD_REQUEST
    error_type = "client_error"

class ServerError(AppException):
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    error_type = "server_error"
