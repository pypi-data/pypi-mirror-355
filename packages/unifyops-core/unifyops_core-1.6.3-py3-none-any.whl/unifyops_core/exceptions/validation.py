from http import HTTPStatus
from .base import ClientError

class FieldValidationError(ClientError):
    """Single-field validation failure."""
    def __init__(self, field: str, message: str, *, details=None):
        d = [{"loc": [field], "msg": message, "type": "value_error"}] if details is None else details
        super().__init__(message, status_code=HTTPStatus.UNPROCESSABLE_ENTITY, details=d, error_type="field_validation_error")

class SchemaValidationError(ClientError):
    """Complex payload validation failure."""
    def __init__(self, message="Schema validation error", *, details=None):
        super().__init__(message, status_code=HTTPStatus.UNPROCESSABLE_ENTITY, details=details, error_type="schema_validation_error")
