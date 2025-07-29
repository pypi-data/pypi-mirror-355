from http import HTTPStatus
from .base import ClientError

class ApiClientError(ClientError):
    """Raised when configuration or request formatting is invalid."""
    def __init__(self, message="Invalid API client configuration", *, details=None):
        super().__init__(
            message,
            status_code=HTTPStatus.BAD_REQUEST,
            details=details,
            error_type="api_client_error"
        )

class ApiResponseError(ClientError):
    """Raised when an external API returns an unexpected status."""
    def __init__(self, message="Bad response from external API", *, status_code=None, details=None):
        super().__init__(
            message,
            status_code=status_code or HTTPStatus.BAD_GATEWAY,
            details=details,
            error_type="api_response_error"
        )
