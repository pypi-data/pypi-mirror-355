from .base import ClientError

class ConfigurationError(ClientError):
    """Application mis-configuration."""
    def __init__(self, message="Configuration error", *, details=None):
        super().__init__(message, details=details, error_type="config_error")

class DependencyError(ClientError):
    """Missing or invalid dependency."""
    def __init__(self, message="Dependency error", *, details=None):
        super().__init__(message, details=details, error_type="dependency_error")
