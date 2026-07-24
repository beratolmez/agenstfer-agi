from __future__ import annotations

from collections.abc import Awaitable, Callable
from time import perf_counter

from fastapi import Request
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.metrics import set_meter_provider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

_configured = False


def configure_observability(endpoint: str | None) -> None:
    """Configure opt-in OTLP exporters; telemetry never contains sensitive payloads or secrets."""
    global _configured
    if _configured or not endpoint:
        return
    base = endpoint.rstrip("/")
    resource = Resource.create({"service.name": "agi-control-plane"})

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{base}/v1/traces"))
    )
    trace.set_tracer_provider(tracer_provider)

    metric_reader = PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=f"{base}/v1/metrics"))
    set_meter_provider(MeterProvider(resource=resource, metric_readers=[metric_reader]))
    _configured = True


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """HTTP middleware recording content-safe metrics and traces.

    PROHIBITED FROM SPANS/METRICS BY POLICY:
    - Prompts, completion text, or model outputs
    - Raw source bodies or evidence excerpts
    - Secrets, passwords, or tokens
    - PII, emails, or contact identifiers
    """

    def __init__(self, app):
        super().__init__(app)
        meter = metrics.get_meter("agi.http")
        self.requests = meter.create_counter("agi.http.requests")
        self.duration = meter.create_histogram("agi.http.duration", unit="ms")
        self.tracer = trace.get_tracer("agi.http")

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        started = perf_counter()
        status_code = 500
        # Deliberately exclude query strings, bodies, headers, prompts, and secrets.
        with self.tracer.start_as_current_span("http.request") as span:
            span.set_attribute("http.request.method", request.method)
            try:
                response = await call_next(request)
                status_code = response.status_code
                return response
            finally:
                route = request.scope.get("route")
                route_path = getattr(route, "path", "unmatched")
                request_id = getattr(request.state, "request_id", "unassigned")
                attributes = {
                    "http.request.method": request.method,
                    "http.route": route_path,
                    "http.response.status_code": status_code,
                }
                span.set_attribute("http.route", route_path)
                span.set_attribute("http.response.status_code", status_code)
                span.set_attribute("agi.request_id", request_id)
                self.requests.add(1, attributes)
                self.duration.record((perf_counter() - started) * 1000, attributes)
