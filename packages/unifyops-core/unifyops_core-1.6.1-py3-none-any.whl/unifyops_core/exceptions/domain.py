from .base import ClientError

class DomainError(ClientError):
    """Business-rule violation or invalid domain operation."""
    def __init__(self, message="Domain operation failed", *, details=None):
        super().__init__(message, details=details, error_type="domain_error")
