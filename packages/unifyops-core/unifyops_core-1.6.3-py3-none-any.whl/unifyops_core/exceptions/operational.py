from .base import ServerError

class TimeoutError(ServerError):
    """Operation timed out."""
    def __init__(self, message="Operation timed out", *, details=None):
        super().__init__(message, details=details, error_type="timeout_error")

class CircuitBreakerError(ServerError):
    """Circuit breaker tripped."""
    def __init__(self, message="Circuit breaker open", *, details=None):
        super().__init__(message, details=details, error_type="circuit_breaker_error")
