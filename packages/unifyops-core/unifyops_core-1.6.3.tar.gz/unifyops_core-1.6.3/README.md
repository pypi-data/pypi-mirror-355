# UnifyOps Core

Core utilities for UnifyOps Python projects. This package provides shared functionality that can be used across all UnifyOps Python applications.

## Features

- **Logging**: Standardized logging configuration with JSON support and OpenTelemetry integration
- **Exceptions**: Common exception classes with proper HTTP status code mapping
- **OpenTelemetry**: Centralized observability setup for tracing and logging

## Installation

### Basic Installation

```bash
pip install unifyops-core
```

### With OpenTelemetry Support

For observability and monitoring with Signoz:

```bash
# Basic OpenTelemetry support
pip install unifyops-core[otel]

# Full FastAPI + OpenTelemetry support (recommended for APIs)
pip install unifyops-core[fastapi-otel]

# All optional dependencies
pip install unifyops-core[all]
```

### Using Pipenv

```toml
# In your Pipfile
[packages]
unifyops-core = {extras = ["fastapi-otel"], version = "*"}
```

Then install with:

```bash
pipenv install
```

## Usage

### OpenTelemetry Setup (New!)

Replace complex OpenTelemetry setup in your service with a single function call:

```python
from unifyops_core.logging import setup_otel_for_service

# Simple setup - replaces 40+ lines of boilerplate
otel_success = setup_otel_for_service(
    service_name="my-api",
    service_version="1.0.0",
    environment="production",
    additional_resource_attributes={
        "team": "backend",
        "domain": "user-management"
    }
)
```

### Logging

```python
from unifyops_core.logging import get_logger

# Create a standard logger
logger = get_logger("my_app")
logger.info("This is a log message")

# Create a JSON logger
json_logger = get_logger("my_app.json", json_format=True)
json_logger.info("This is a structured log", extra={"props": {"user_id": "123", "action": "login"}})

# Log with context
from unifyops_core.logging import log_with_context
log_with_context(logger, logger.INFO, "User logged in", user_id="123", action="login")
```

### Exceptions

```python
from unifyops_core.exceptions import NotFoundError, ValidationError

# Raise standard exceptions
raise NotFoundError("User not found")
raise ValidationError("Invalid email format", details={"email": "Invalid format"})

# Custom exception with details
from unifyops_core.exceptions import UnifyOpsException
raise UnifyOpsException(
    message="Payment processing failed",
    code="PAYMENT_ERROR",
    status_code=400,
    details={"payment_id": "123", "reason": "Insufficient funds"}
)
```

## Installation Options

| Extra          | Description                             | Use Case                                 |
| -------------- | --------------------------------------- | ---------------------------------------- |
| `otel`         | Basic OpenTelemetry support             | Services needing observability           |
| `fastapi-otel` | FastAPI + OpenTelemetry instrumentation | FastAPI applications                     |
| `all`          | All optional dependencies               | Development or full-featured deployments |

## License

This project is licensed under the MIT License.
