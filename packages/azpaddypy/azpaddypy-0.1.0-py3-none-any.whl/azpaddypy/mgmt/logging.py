import logging
import os
import json
import functools
import time
from typing import Optional, Dict, Any, Union, List
from datetime import datetime
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode, Span
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource


class AzureLogger:
    """
    Comprehensive logging class for Azure Functions and Azure Web Apps
    using Azure Monitor OpenTelemetry integration with advanced tracing capabilities.
    """

    def __init__(
        self,
        service_name: str,
        service_version: str = "1.0.0",
        connection_string: Optional[str] = None,
        log_level: int = logging.INFO,
        enable_console_logging: bool = True,
        custom_resource_attributes: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize the Azure Logger with OpenTelemetry tracing

        Args:
            service_name: Name of your service/application
            service_version: Version of your service
            connection_string: Application Insights connection string
            log_level: Logging level (default: INFO)
            enable_console_logging: Enable console output for local development
            custom_resource_attributes: Additional resource attributes
        """
        self.service_name = service_name
        self.service_version = service_version
        self.connection_string = connection_string or os.getenv(
            "APPLICATIONINSIGHTS_CONNECTION_STRING"
        )

        # Prepare resource attributes
        resource_attributes = {
            "service.name": service_name,
            "service.version": service_version,
            "service.instance.id": os.getenv("WEBSITE_INSTANCE_ID", "local"),
        }

        if custom_resource_attributes:
            resource_attributes.update(custom_resource_attributes)

        # Configure Azure Monitor if connection string is available
        if self.connection_string:
            try:
                configure_azure_monitor(
                    connection_string=self.connection_string,
                    resource_attributes=resource_attributes,
                    enable_live_metrics=True,
                )
                self._telemetry_enabled = True
            except Exception as e:
                print(f"Warning: Failed to configure Azure Monitor: {e}")
                self._telemetry_enabled = False
        else:
            self._telemetry_enabled = False
            print(
                "Warning: No Application Insights connection string found. Telemetry disabled."
            )

        # Set up logger without instrumentor
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(log_level)

        # Clear existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Add console handler for local development
        if enable_console_logging:
            self._setup_console_handler()

        # Get tracer for manual span creation
        self.tracer = trace.get_tracer(__name__)

        # Initialize correlation context
        self._correlation_id = None

        self.info(
            f"Azure Logger initialized for service '{service_name}' v{service_version}"
        )

    def _setup_console_handler(self):
        """Setup console logging handler with structured format"""
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d"
        )
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for request tracking"""
        self._correlation_id = correlation_id

    def get_correlation_id(self) -> Optional[str]:
        """Get current correlation ID"""
        return self._correlation_id

    def _enhance_extra(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Enhance log extra data with correlation and service info"""
        enhanced_extra = {
            "service_name": self.service_name,
            "service_version": self.service_version,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if self._correlation_id:
            enhanced_extra["correlation_id"] = self._correlation_id

        # Add span context if available
        current_span = trace.get_current_span()
        if current_span and current_span.is_recording():
            span_context = current_span.get_span_context()
            enhanced_extra["trace_id"] = format(span_context.trace_id, "032x")
            enhanced_extra["span_id"] = format(span_context.span_id, "016x")

        if extra:
            enhanced_extra.update(extra)

        return enhanced_extra

    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log debug message with enhanced context"""
        self.logger.debug(message, extra=self._enhance_extra(extra))

    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log info message with enhanced context"""
        self.logger.info(message, extra=self._enhance_extra(extra))

    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log warning message with enhanced context"""
        self.logger.warning(message, extra=self._enhance_extra(extra))

    def error(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: bool = True,
    ):
        """Log error message with enhanced context and exception info"""
        self.logger.error(message, extra=self._enhance_extra(extra), exc_info=exc_info)

    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log critical message with enhanced context"""
        self.logger.critical(message, extra=self._enhance_extra(extra))

    def log_function_execution(
        self,
        function_name: str,
        duration_ms: float,
        success: bool = True,
        extra: Optional[Dict[str, Any]] = None,
    ):
        """
        Log function execution metrics with performance data

        Args:
            function_name: Name of the executed function
            duration_ms: Execution duration in milliseconds
            success: Whether the function executed successfully
            extra: Additional custom properties
        """
        log_data = {
            "function_name": function_name,
            "duration_ms": duration_ms,
            "success": success,
            "performance_category": "function_execution",
        }

        if extra:
            log_data.update(extra)

        log_level = logging.INFO if success else logging.ERROR
        message = f"Function '{function_name}' executed in {duration_ms:.2f}ms - {'SUCCESS' if success else 'FAILED'}"

        if success:
            self.info(message, extra=log_data)
        else:
            self.error(message, extra=log_data, exc_info=False)

    def log_request(
        self,
        method: str,
        url: str,
        status_code: int,
        duration_ms: float,
        extra: Optional[Dict[str, Any]] = None,
    ):
        """
        Log HTTP request with comprehensive details

        Args:
            method: HTTP method
            url: Request URL
            status_code: HTTP status code
            duration_ms: Request duration in milliseconds
            extra: Additional custom properties
        """
        log_data = {
            "http_method": method,
            "http_url": str(url),
            "http_status_code": status_code,
            "duration_ms": duration_ms,
            "request_category": "http_request",
        }

        if extra:
            log_data.update(extra)

        # Determine log level based on status code
        if status_code < 400:
            log_level = logging.INFO
            status_text = "SUCCESS"
        elif status_code < 500:
            log_level = logging.WARNING
            status_text = "CLIENT_ERROR"
        else:
            log_level = logging.ERROR
            status_text = "SERVER_ERROR"

        message = (
            f"{method} {url} - {status_code} - {duration_ms:.2f}ms - {status_text}"
        )
        self.logger.log(log_level, message, extra=self._enhance_extra(log_data))

    def create_span(
        self,
        span_name: str,
        attributes: Optional[Dict[str, Union[str, int, float, bool]]] = None,
    ) -> Span:
        """
        Create a new span for distributed tracing

        Args:
            span_name: Name of the span
            attributes: Initial attributes for the span

        Returns:
            OpenTelemetry span context manager
        """
        span = self.tracer.start_span(span_name)

        # Add default attributes
        span.set_attribute("service.name", self.service_name)
        span.set_attribute("service.version", self.service_version)

        if self._correlation_id:
            span.set_attribute("correlation.id", self._correlation_id)

        # Add custom attributes
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)

        return span

    def trace_function(
        self,
        function_name: Optional[str] = None,
        log_args: bool = False,
        log_result: bool = False,
        log_execution: bool = True,
    ):
        """
        Decorator to automatically trace function execution with comprehensive logging

        Args:
            function_name: Custom name for the span (defaults to function name)
            log_args: Whether to log function arguments
            log_result: Whether to log function result
            log_execution: Whether to log execution metrics
        """

        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                span_name = function_name or f"{func.__module__}.{func.__name__}"

                with self.tracer.start_as_current_span(span_name) as span:
                    # Add function metadata
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)
                    span.set_attribute("service.name", self.service_name)

                    if self._correlation_id:
                        span.set_attribute("correlation.id", self._correlation_id)

                    if log_args and args:
                        span.set_attribute("function.args_count", len(args))
                    if log_args and kwargs:
                        span.set_attribute("function.kwargs_count", len(kwargs))

                    start_time = time.time()

                    try:
                        self.debug(f"Starting function execution: {func.__name__}")

                        result = func(*args, **kwargs)
                        duration_ms = (time.time() - start_time) * 1000

                        # Mark span as successful
                        span.set_attribute("function.duration_ms", duration_ms)
                        span.set_attribute("function.success", True)
                        span.set_status(Status(StatusCode.OK))

                        if log_result and result is not None:
                            span.set_attribute("function.has_result", True)
                            span.set_attribute(
                                "function.result_type", type(result).__name__
                            )

                        if log_execution:
                            self.log_function_execution(
                                func.__name__,
                                duration_ms,
                                True,
                                {
                                    "args_count": len(args) if args else 0,
                                    "kwargs_count": len(kwargs) if kwargs else 0,
                                },
                            )

                        self.debug(f"Function execution completed: {func.__name__}")
                        return result

                    except Exception as e:
                        duration_ms = (time.time() - start_time) * 1000

                        # Mark span as failed
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.record_exception(e)
                        span.set_attribute("function.duration_ms", duration_ms)
                        span.set_attribute("function.success", False)
                        span.set_attribute("error.type", type(e).__name__)
                        span.set_attribute("error.message", str(e))

                        if log_execution:
                            self.log_function_execution(
                                func.__name__,
                                duration_ms,
                                False,
                                {
                                    "error_type": type(e).__name__,
                                    "error_message": str(e),
                                },
                            )

                        self.error(
                            f"Function execution failed: {func.__name__} - {str(e)}"
                        )
                        raise

            return wrapper

        return decorator

    def add_span_attributes(self, attributes: Dict[str, Union[str, int, float, bool]]):
        """Add attributes to the current active span"""
        current_span = trace.get_current_span()
        if current_span and current_span.is_recording():
            for key, value in attributes.items():
                current_span.set_attribute(key, value)

    def add_span_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Add an event to the current active span"""
        current_span = trace.get_current_span()
        if current_span and current_span.is_recording():
            event_attributes = attributes or {}
            if self._correlation_id:
                event_attributes["correlation_id"] = self._correlation_id
            current_span.add_event(name, event_attributes)

    def set_span_status(
        self, status_code: StatusCode, description: Optional[str] = None
    ):
        """Set the status of the current active span"""
        current_span = trace.get_current_span()
        if current_span and current_span.is_recording():
            current_span.set_status(Status(status_code, description))

    def log_with_span(
        self,
        span_name: str,
        message: str,
        level: int = logging.INFO,
        extra: Optional[Dict[str, Any]] = None,
        span_attributes: Optional[Dict[str, Union[str, int, float, bool]]] = None,
    ):
        """
        Log a message within a span context

        Args:
            span_name: Name of the span
            message: Log message
            level: Log level
            extra: Additional log properties
            span_attributes: Attributes to add to the span
        """
        with self.tracer.start_as_current_span(span_name) as span:
            if span_attributes:
                for key, value in span_attributes.items():
                    span.set_attribute(key, value)

            self.logger.log(level, message, extra=self._enhance_extra(extra))

    def log_dependency(
        self,
        dependency_type: str,
        name: str,
        command: str,
        success: bool,
        duration_ms: float,
        extra: Optional[Dict[str, Any]] = None,
    ):
        """
        Log external dependency calls (Database, HTTP, etc.)

        Args:
            dependency_type: Type of dependency (SQL, HTTP, etc.)
            name: Name/identifier of the dependency
            command: Command/query executed
            success: Whether the call was successful
            duration_ms: Call duration in milliseconds
            extra: Additional properties
        """
        log_data = {
            "dependency_type": dependency_type,
            "dependency_name": name,
            "dependency_command": command,
            "dependency_success": success,
            "duration_ms": duration_ms,
            "category": "dependency_call",
        }

        if extra:
            log_data.update(extra)

        log_level = logging.INFO if success else logging.ERROR
        status = "SUCCESS" if success else "FAILED"
        message = f"Dependency call: {dependency_type}:{name} - {duration_ms:.2f}ms - {status}"

        self.logger.log(log_level, message, extra=self._enhance_extra(log_data))

    def flush(self):
        """Flush all pending telemetry data"""
        if self._telemetry_enabled:
            try:
                # Force flush any pending telemetry
                from opentelemetry.sdk.trace import TracerProvider

                tracer_provider = trace.get_tracer_provider()
                if hasattr(tracer_provider, "force_flush"):
                    tracer_provider.force_flush(timeout_millis=5000)
            except Exception as e:
                self.warning(f"Failed to flush telemetry: {e}")


# Factory functions for easy instantiation
def create_app_logger(
    service_name: str,
    service_version: str = "1.0.0",
    connection_string: Optional[str] = None,
    log_level: int = logging.INFO,
    enable_console_logging: bool = True,
    custom_resource_attributes: Optional[Dict[str, str]] = None,
) -> AzureLogger:
    """
    Factory function to create an AzureLogger instance

    Args:
        service_name: Name of your service/application
        service_version: Version of your service
        connection_string: Application Insights connection string
        log_level: Logging level
        enable_console_logging: Enable console output
        custom_resource_attributes: Additional resource attributes

    Returns:
        Configured AzureLogger instance
    """
    return AzureLogger(
        service_name=service_name,
        service_version=service_version,
        connection_string=connection_string,
        log_level=log_level,
        enable_console_logging=enable_console_logging,
        custom_resource_attributes=custom_resource_attributes,
    )


def create_function_logger(
    function_app_name: str,
    function_name: str,
    service_version: str = "1.0.0",
    connection_string: Optional[str] = None,
) -> AzureLogger:
    """
    Factory function specifically for Azure Functions

    Args:
        function_app_name: Name of the Function App
        function_name: Name of the specific function
        service_version: Version of the service
        connection_string: Application Insights connection string

    Returns:
        Configured AzureLogger instance for Azure Functions
    """
    custom_attributes = {
        "azure.function.app": function_app_name,
        "azure.function.name": function_name,
        "azure.resource.type": "function",
    }

    return create_app_logger(
        service_name=f"{function_app_name}.{function_name}",
        service_version=service_version,
        connection_string=connection_string,
        custom_resource_attributes=custom_attributes,
    )
