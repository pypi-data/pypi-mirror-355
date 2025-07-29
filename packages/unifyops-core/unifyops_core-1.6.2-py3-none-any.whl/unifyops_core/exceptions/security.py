from http import HTTPStatus
from .base import ClientError

class AuthenticationError(ClientError):
    """Authentication failure."""
    def __init__(self, message="Authentication failed", *, details=None):
        super().__init__(message, status_code=HTTPStatus.UNAUTHORIZED, details=details, error_type="auth_error")

class AuthorizationError(ClientError):
    """Insufficient permissions."""
    def __init__(self, message="Forbidden", *, details=None):
        super().__init__(message, status_code=HTTPStatus.FORBIDDEN, details=details, error_type="authz_error")

class TokenExpiredError(AuthenticationError):
    """JWT or session expired."""
    def __init__(self, message="Token expired", *, details=None):
        super().__init__(message, details=details, error_type="token_expired")

class TokenInvalidError(AuthenticationError):
    """JWT is invalid."""
    def __init__(self, message="Invalid token", *, details=None):
        super().__init__(message, details=details, error_type="token_invalid")
