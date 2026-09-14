from __future__ import annotations

from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor, SpanExporter


def build_tracer_provider(exporter: SpanExporter | None = None, service_name: str = "agent-runtime") -> TracerProvider:
    """A dedicated TracerProvider instance — deliberately NOT the OTel
    global singleton, so tests (and, later, multiple agents in one
    process) each get their own isolated provider instead of fighting
    over global state.

    Defaults to printing spans to the console. Pass an OTLP exporter (see
    build_otlp_exporter below) to send to a real local Collector instead."""
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(SimpleSpanProcessor(exporter or ConsoleSpanExporter()))
    return provider


def build_otlp_exporter(endpoint: str = "http://localhost:4318/v1/traces") -> SpanExporter:
    """An exporter that sends real OTLP/HTTP to a Collector — e.g. the one
    started with observation/collector/otel-collector-config.yaml."""
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

    return OTLPSpanExporter(endpoint=endpoint)
