"""
OpenTelemetry Integration for Signoz

This module provides OpenTelemetry integration for log correlation and service
attribution in Signoz.

Usage:
    from unifyops_core.logging.otel_integration import setup_otel_for_service
    success = setup_otel_for_service("identity-api", "1.0.0", "production")
"""

import os
import logging
import platform
import uuid
from typing import Optional, Dict, Any

# Try to import OpenTelemetry components - gracefully handle missing packages
try:
    from opentelemetry import _logs, trace
    from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False

# Configuration defaults
DEFAULT_SERVICE_NAME = "unifyops-api"
DEFAULT_SERVICE_VERSION = "1.0.0" 
DEFAULT_SERVICE_NAMESPACE = "unifyops"
DEFAULT_ENVIRONMENT = "development"
# Use DaemonSet collector for node-local collection - better for distributed logs
DEFAULT_OTLP_ENDPOINT = "http://otel-collector-daemonset.observability.svc.cluster.local:4318"
DEFAULT_LOG_LEVEL = "INFO"


class ResourceBuilder:
    """Builder for OpenTelemetry resource attributes."""
    
    def __init__(self):
        self.attributes = {}
    
    def add_service_info(self) -> "ResourceBuilder":
        """Add core service attributes."""
        self.attributes.update({
            "service.name": os.getenv("SERVICE_NAME", DEFAULT_SERVICE_NAME),
            "service.version": os.getenv("SERVICE_VERSION", DEFAULT_SERVICE_VERSION),
            "service.namespace": os.getenv("SERVICE_NAMESPACE", DEFAULT_SERVICE_NAMESPACE),
            "service.instance.id": self._get_instance_id(),
            "deployment.environment": os.getenv("DEPLOYMENT_ENVIRONMENT", 
                                               os.getenv("ENVIRONMENT", DEFAULT_ENVIRONMENT))
        })
        return self
    
    def add_host_info(self) -> "ResourceBuilder":
        """Add host and OS attributes."""
        self.attributes.update({
            "host.name": os.getenv("HOSTNAME", platform.node()),
            "host.type": self._get_host_type(),
            "host.arch": platform.machine(),
            "os.type": platform.system().lower(),
            "os.name": platform.system(),
            "os.version": platform.release()
        })
        return self
    
    def add_process_info(self) -> "ResourceBuilder":
        """Add process and runtime attributes."""
        self.attributes.update({
            "process.pid": os.getpid(),
            "process.runtime.name": "python",
            "process.runtime.version": platform.python_version(),
            "telemetry.sdk.language": "python",
            "telemetry.sdk.name": "opentelemetry"
        })
        return self
    
    def add_kubernetes_info(self) -> "ResourceBuilder":
        """Add Kubernetes attributes if available."""
        k8s_attrs = {
            "k8s.pod.name": os.getenv("K8S_POD_NAME"),
            "k8s.pod.uid": os.getenv("K8S_POD_UID"),
            "k8s.namespace.name": os.getenv("K8S_NAMESPACE_NAME"),
            "k8s.node.name": os.getenv("K8S_NODE_NAME"),
            "k8s.cluster.name": os.getenv("K8S_CLUSTER_NAME"),
            "container.name": os.getenv("CONTAINER_NAME"),
            "container.id": os.getenv("CONTAINER_ID")
        }
        # Only add non-None values
        self.attributes.update({k: v for k, v in k8s_attrs.items() if v})
        return self
    
    def add_cloud_info(self) -> "ResourceBuilder":
        """Add cloud provider attributes if available."""
        cloud_provider = os.getenv("CLOUD_PROVIDER")
        if cloud_provider:
            self.attributes.update({
                "cloud.provider": cloud_provider,
                "cloud.region": os.getenv("CLOUD_REGION"),
                "cloud.availability_zone": os.getenv("CLOUD_AVAILABILITY_ZONE")
            })
        return self
    
    def build(self) -> Optional["Resource"]:
        """Build the Resource object."""
        if not OTEL_AVAILABLE:
            return None
        
        # Filter out None values
        clean_attrs = {k: v for k, v in self.attributes.items() if v is not None}
        return Resource.create(clean_attrs)
    
    def _get_instance_id(self) -> str:
        """Generate or retrieve service instance ID."""
        # Check environment variable first
        if instance_id := os.getenv("SERVICE_INSTANCE_ID"):
            return instance_id
        
        # Use pod UID if in Kubernetes
        if pod_uid := os.getenv("K8S_POD_UID"):
            namespace_uuid = uuid.UUID("4d63009a-8d0f-11ee-aad7-4c796ed8e320")
            return str(uuid.uuid5(namespace_uuid, pod_uid))
        
        # Generate random UUID
        return str(uuid.uuid4())
    
    def _get_host_type(self) -> str:
        """Determine host type based on environment."""
        if os.getenv("KUBERNETES_SERVICE_HOST"):
            return "container"
        return os.getenv("HOST_TYPE", "physical")


def create_otel_resource() -> Optional["Resource"]:
    """Create OpenTelemetry Resource with all required attributes."""
    return (ResourceBuilder()
            .add_service_info()
            .add_host_info()
            .add_process_info()
            .add_kubernetes_info()
            .add_cloud_info()
            .build())


def get_otlp_endpoint() -> str:
    """Get OTLP endpoint from environment or use default."""
    return (os.getenv("OTEL_EXPORTER_OTLP_LOGS_ENDPOINT") or
            os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT") or
            os.getenv("SIGNOZ_ENDPOINT") or
            DEFAULT_OTLP_ENDPOINT)


def get_otlp_headers() -> Dict[str, str]:
    """Get headers for OTLP exporter."""
    headers = {}
    
    # Parse environment headers
    if env_headers := os.getenv("OTEL_EXPORTER_OTLP_HEADERS"):
        for header_pair in env_headers.split(","):
            if "=" in header_pair:
                key, value = header_pair.strip().split("=", 1)
                headers[key] = value
    
    # Add Signoz access token if available
    if token := os.getenv("SIGNOZ_ACCESS_TOKEN"):
        headers["signoz-access-token"] = token
    
    return headers


def setup_otel_for_service(
    service_name: str,
    service_version: str = "1.0.0",
    environment: str = "development",
    enable_tracing: bool = True,
    enable_logging: bool = True,
    enable_console_logs: bool = True,
    log_level: str = DEFAULT_LOG_LEVEL,
    additional_resource_attributes: Optional[Dict[str, str]] = None
) -> bool:
    """
    Comprehensive OpenTelemetry setup for UnifyOps services.
    
    This function handles both tracing and logging setup with fallback mechanisms.
    It consolidates all OpenTelemetry configuration that would otherwise be 
    duplicated across service main.py files.
    
    Before (40+ lines of complex setup in each service):
    ```python
    otel_success = False
    try:
        import opentelemetry
        from opentelemetry.sdk.resources import Resource
        try:
            from unifyops_core.logging.otel_integration import setup_otel_logging
            otel_success = setup_otel_logging()
            # ... more complex fallback logic
        except ImportError:
            print("⚠️  unifyops_core OpenTelemetry integration not available, using basic setup")
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider
            # ... 30+ more lines of setup code
    except ImportError as e:
        print(f"Warning: OpenTelemetry packages not available...")
        otel_success = False
    ```
    
    After (simple one-liner in each service):
    ```python
    from unifyops_core.logging import setup_otel_for_service
    otel_success = setup_otel_for_service(
        service_name=settings.SERVICE_NAME,
        service_version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        additional_resource_attributes={
            "api_type": "gateway", 
            "domain": "identity"
        }
    )
    ```
    
    Args:
        service_name: Name of the service (e.g., "identity-api")
        service_version: Version of the service
        environment: Deployment environment (dev, staging, prod)
        enable_tracing: Whether to set up distributed tracing
        enable_logging: Whether to set up log export to Signoz
        enable_console_logs: Whether to also enable console logging
        log_level: Minimum log level for OpenTelemetry logging
        additional_resource_attributes: Extra attributes to add to the resource
        
    Returns:
        bool: True if setup successful, False if using fallback logging
        
    Examples:
        Basic setup:
        >>> success = setup_otel_for_service("user-api", "2.1.0", "production")
        
        With custom attributes:
        >>> success = setup_otel_for_service(
        ...     "payment-service",
        ...     "1.0.0", 
        ...     "staging",
        ...     additional_resource_attributes={
        ...         "team": "payments",
        ...         "criticality": "high"
        ...     }
        ... )
        
        Logging-only setup:
        >>> success = setup_otel_for_service(
        ...     "background-worker",
        ...     enable_tracing=False,
        ...     enable_logging=True
        ... )
    """
    if not OTEL_AVAILABLE:
        print("⚠️  OpenTelemetry packages not available. Install with: pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp")
        return False
    
    success = True
    
    try:
        # Override service attributes for this specific service
        os.environ["SERVICE_NAME"] = service_name
        os.environ["SERVICE_VERSION"] = service_version
        os.environ["ENVIRONMENT"] = environment
        
        # Create enhanced resource with additional attributes
        resource = create_otel_resource()
        if additional_resource_attributes:
            # Create new resource with additional attributes
            all_attributes = dict(resource.attributes)
            all_attributes.update(additional_resource_attributes)
            resource = Resource.create(all_attributes)
        
        if not resource:
            print("⚠️  Failed to create OpenTelemetry resource")
            return False
        
        # Setup tracing if enabled
        if enable_tracing:
            tracing_success = _setup_tracing(resource, service_name)
            if tracing_success:
                print(f"✅ OpenTelemetry tracing configured for {service_name}")
            else:
                print(f"⚠️  OpenTelemetry tracing setup failed for {service_name}")
                success = False
        
        # Setup logging if enabled
        if enable_logging:
            logging_success = _setup_logging_internal(
                resource, enable_console_logs, log_level
            )
            if logging_success:
                print(f"✅ OpenTelemetry logging configured for {service_name}")
            else:
                print(f"⚠️  OpenTelemetry logging setup failed for {service_name}")
                success = False
        
        if success:
            print(f"✅ OpenTelemetry fully configured for {service_name} in {environment}")
        else:
            print(f"⚠️  OpenTelemetry partially configured for {service_name}, using fallback where needed")
        
        return success
        
    except Exception as e:
        print(f"⚠️  OpenTelemetry setup error for {service_name}: {e}, using fallback logging")
        return False


def _setup_tracing(resource: "Resource", service_name: str) -> bool:
    """
    Setup OpenTelemetry tracing with OTLP export.
    
    Args:
        resource: OpenTelemetry Resource with service attributes
        service_name: Name of the service for logging
        
    Returns:
        bool: True if tracing setup successful
    """
    try:
        # Set up tracer provider
        tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(tracer_provider)
        
        # Get OTLP endpoint for tracing
        otlp_endpoint = (os.getenv('OTEL_EXPORTER_OTLP_TRACES_ENDPOINT') or
                        os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT') or
                        get_otlp_endpoint())
        
        if otlp_endpoint:
            # Create OTLP exporter with proper configuration
            otlp_exporter = OTLPSpanExporter(
                endpoint=otlp_endpoint,
                insecure=os.getenv("OTEL_EXPORTER_OTLP_INSECURE", "true").lower() == "true",
                headers=get_otlp_headers()
            )
            
            # Add span processor
            span_processor = BatchSpanProcessor(otlp_exporter)
            tracer_provider.add_span_processor(span_processor)
            
            return True
        else:
            print(f"⚠️  No OTLP endpoint configured for {service_name}, skipping trace export")
            return False
            
    except Exception as e:
        print(f"⚠️  Failed to setup tracing for {service_name}: {e}")
        return False


def _setup_logging_internal(
    resource: "Resource", 
    enable_console_logs: bool, 
    log_level: str
) -> bool:
    """
    Internal function to setup OpenTelemetry logging.
    
    Args:
        resource: OpenTelemetry Resource with service attributes
        enable_console_logs: Whether to also enable console logging
        log_level: Minimum log level
        
    Returns:
        bool: True if logging setup successful
    """
    try:
        # Get endpoint for logging
        endpoint = get_otlp_endpoint()
        
        # Create OTLP log exporter
        exporter = OTLPLogExporter(
            endpoint=endpoint,
            insecure=os.getenv("OTEL_EXPORTER_OTLP_INSECURE", "true").lower() == "true",
            headers=get_otlp_headers()
        )
        
        # Create logger provider
        provider = LoggerProvider(resource=resource)
        provider.add_log_record_processor(
            BatchLogRecordProcessor(exporter)
        )
        
        # Set global logger provider
        _logs.set_logger_provider(provider)
        
        # Create and configure handler
        handler = LoggingHandler(
            level=getattr(logging, log_level.upper()),
            logger_provider=provider
        )
        
        # Configure root logger
        root_logger = logging.getLogger()
        # Always preserve console logs for debugging - add OTLP handler without clearing existing handlers
        # Only clear handlers if explicitly disabled AND we're in a local environment
        if not enable_console_logs and os.getenv("ENVIRONMENT", "local").lower() in ("local", "test"):
            root_logger.handlers.clear()
        root_logger.addHandler(handler)
        root_logger.setLevel(getattr(logging, log_level.upper()))
        
        return True
        
    except Exception as e:
        print(f"⚠️  Failed to setup OpenTelemetry logging: {e}")
        return False


def verify_otel_setup() -> Dict[str, Any]:
    """Verify OpenTelemetry setup and return status information."""
    if not OTEL_AVAILABLE:
        return {
            "status": "unavailable",
            "error": "OpenTelemetry packages not installed"
        }
    
    try:
        provider = _logs.get_logger_provider()
        resource = getattr(provider, '_resource', None)
        
        if resource:
            return {
                "status": "configured",
                "service_name": resource.attributes.get("service.name"),
                "service_instance_id": resource.attributes.get("service.instance.id"),
                "attributes": dict(resource.attributes)
            }
        else:
            return {
                "status": "not_configured",
                "error": "No resource configured"
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def setup_otel_logging(
    signoz_endpoint: Optional[str] = None,
    enable_console_logs: bool = True,
    log_level: str = DEFAULT_LOG_LEVEL
) -> bool:
    """
    Legacy function for backward compatibility.
    Use setup_otel_for_service() for new implementations.
    
    Set up OpenTelemetry logging with Signoz integration.
    
    Args:
        signoz_endpoint: Signoz OTLP endpoint (auto-detected if not provided)
        enable_console_logs: Whether to also enable console logging
        log_level: Minimum log level
        
    Returns:
        True if setup successful, False otherwise
    """
    # Use the new comprehensive setup function with logging only
    return setup_otel_for_service(
        service_name=os.getenv("SERVICE_NAME", DEFAULT_SERVICE_NAME),
        service_version=os.getenv("SERVICE_VERSION", DEFAULT_SERVICE_VERSION),
        environment=os.getenv("ENVIRONMENT", DEFAULT_ENVIRONMENT),
        enable_tracing=False,  # Legacy function only does logging
        enable_logging=True,
        enable_console_logs=enable_console_logs,
        log_level=log_level
    )


# Auto-setup if requested
if os.getenv("AUTO_SETUP_OTEL", "false").lower() == "true":
    service_name = os.getenv("SERVICE_NAME", DEFAULT_SERVICE_NAME)
    setup_otel_for_service(service_name) 