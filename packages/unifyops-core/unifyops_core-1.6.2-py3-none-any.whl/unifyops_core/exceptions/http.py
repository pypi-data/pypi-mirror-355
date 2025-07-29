from http import HTTPStatus
from .base import ClientError, ServerError

class NotFoundError(ClientError):
    def __init__(self, message="Not found", *, details=None):
        super().__init__(message, status_code=HTTPStatus.NOT_FOUND, details=details, error_type="http_not_found")

class UnauthorizedError(ClientError):
    def __init__(self, message="Unauthorized", *, details=None):
        super().__init__(message, status_code=HTTPStatus.UNAUTHORIZED, details=details, error_type="http_unauthorized")

class BadGatewayError(ServerError):
    def __init__(self, message="Bad gateway", *, details=None):
        super().__init__(message, status_code=HTTPStatus.BAD_GATEWAY, details=details, error_type="http_bad_gateway")
