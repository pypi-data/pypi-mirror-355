"""
Setup script for the unifyops-core package.
"""

from setuptools import setup, find_packages
import re

# Read version from __init__.py
with open("unifyops_core/__init__.py", "r") as f:
    version_match = re.search(r'^__version__ = ["\']([^"\']*)["\']', f.read(), re.M)
    if version_match:
        version = version_match.group(1)
    else:
        raise RuntimeError("Unable to find version string")

# Read long description from README.md
with open("README.md", "r") as f:
    long_description = f.read()

# Define OpenTelemetry dependencies as an optional extra
otel_requirements = [
    # Core OpenTelemetry packages
    "opentelemetry-api>=1.27.0",
    "opentelemetry-sdk>=1.27.0",
    
    # OTLP Exporter for Signoz
    "opentelemetry-exporter-otlp>=1.27.0",
    
    # Instrumentation packages
    "opentelemetry-instrumentation>=0.48b0",
    
    # Semantic conventions
    "opentelemetry-semantic-conventions>=0.48b0",
    
    # Logging support
    "opentelemetry-instrumentation-logging>=0.48b0",
    
    # gRPC support (required for OTLP exporter)
    "grpcio>=1.59.0",
    "protobuf>=4.21.0",
]

# FastAPI-specific instrumentation (separate extra)
fastapi_otel_requirements = [
    "opentelemetry-instrumentation-fastapi>=0.48b0",
    "opentelemetry-instrumentation-requests>=0.48b0",
    "opentelemetry-instrumentation-sqlalchemy>=0.48b0",
    "opentelemetry-instrumentation-psycopg2>=0.48b0",
    
    # Propagators for trace context
    "opentelemetry-propagator-b3>=1.27.0",
    "opentelemetry-propagator-jaeger>=1.27.0",
]

setup(
    name="unifyops-core",
    version=version,
    packages=find_packages(),
    include_package_data=True,
    description="Core utilities for UnifyOps Python projects",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="UnifyOps Team",
    author_email="admin@unifyops.com",
    url="https://github.com/unifyops/unifyops-core",
    python_requires=">=3.10",
    install_requires=[
        "pydantic>=2.4.0",
    ],
    extras_require={
        # OpenTelemetry observability support
        "otel": otel_requirements,
        
        # Full FastAPI + OpenTelemetry support
        "fastapi-otel": otel_requirements + fastapi_otel_requirements,
        
        # All optional dependencies
        "all": otel_requirements + fastapi_otel_requirements,
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="unifyops, utilities, logging, exceptions, opentelemetry, observability",
) 