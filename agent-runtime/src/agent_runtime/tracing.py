from __future__ import annotations

from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor, SpanExporter


def build_tracer_provider(exporter: SpanExporter | None = None, service_name: str = "agent-runtime") -> TracerProvider:
    """A dedicated TracerProvider instance — deliberately NOT the OTel
    global singleton, so tests (and, later, multiple agents in one
    process) each get their own isolated provider instead of fighting
    over global state.

    Defaults to printing spans to the console, since there's no real OTel
    Collector yet (Step 32 swaps this for a real OTLP exporter)."""
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(SimpleSpanProcessor(exporter or ConsoleSpanExporter()))
    return provider
