"""OpenTelemetry initialization for FastAPI.

Configurable by environment variables (OTEL_SERVICE_NAME, OTEL_EXPORTER_OTLP_ENDPOINT).
Does not block application startup if no exporter endpoint is configured.
"""

import logging

from app.core.config import Settings

logger = logging.getLogger(__name__)


def init_opentelemetry(settings: Settings) -> None:
    """Initialize OpenTelemetry instrumentation for the FastAPI application.

    If OTEL_EXPORTER_OTLP_ENDPOINT is empty or None, the instrumentation
    is still initialized but no export happens (traces stay in memory / no-op).

    Args:
        settings: Application configuration with OTel settings.
    """
    if not settings.OTEL_EXPORTER_OTLP_ENDPOINT:
        logger.info(
            "OpenTelemetry exporter endpoint not configured — "
            "tracing initialized without export"
        )
        return

    try:
        from opentelemetry import trace  # noqa: PLC0415
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (  # noqa: PLC0415
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.resources import Resource  # noqa: PLC0415
        from opentelemetry.sdk.trace import TracerProvider  # noqa: PLC0415
        from opentelemetry.sdk.trace.export import (  # noqa: PLC0415
            BatchSpanProcessor,
        )

        resource = Resource.create({
            "service.name": settings.OTEL_SERVICE_NAME or "activia-trace",
        })

        tracer_provider = TracerProvider(resource=resource)
        span_processor = BatchSpanProcessor(
            OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT),
        )
        tracer_provider.add_span_processor(span_processor)
        trace.set_tracer_provider(tracer_provider)

        logger.info(
            "OpenTelemetry initialized with exporter at %s",
            settings.OTEL_EXPORTER_OTLP_ENDPOINT,
        )
    except ImportError:
        logger.warning(
            "OpenTelemetry exporter packages not installed — "
            "tracing initialized without export"
        )
    except Exception:
        logger.exception("Failed to initialize OpenTelemetry exporter")
