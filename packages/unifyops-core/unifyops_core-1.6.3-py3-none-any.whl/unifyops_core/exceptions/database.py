from http import HTTPStatus
from .base import ClientError, ServerError

class RecordNotFoundError(ClientError):
    """Entity not found in the database."""
    def __init__(self, message="Record not found", *, details=None):
        super().__init__(message, status_code=HTTPStatus.NOT_FOUND, details=details, error_type="db_record_not_found")

class DataIntegrityError(ServerError):
    """Database constraint violation."""
    def __init__(self, message="Data integrity violation", *, details=None):
        super().__init__(message, status_code=HTTPStatus.CONFLICT, details=details, error_type="db_integrity_error")
