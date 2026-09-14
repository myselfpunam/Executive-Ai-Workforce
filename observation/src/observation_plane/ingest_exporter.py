from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence

import psycopg
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

from .event_store import store_event
from .privacy_gate import apply_privacy_gate


def _ns_to_iso(nanoseconds: int) -> str:
    return datetime.fromtimestamp(nanoseconds / 1e9, tz=timezone.utc).isoformat()


def _span_to_raw_dict(span: ReadableSpan) -> dict:
    context = span.get_span_context()
    parent_span_id = None
    if span.parent is not None:
        parent_span_id = format(span.parent.span_id, "016x")

    return {
        "trace_id": format(context.trace_id, "032x"),
        "span_id": format(context.span_id, "016x"),
        "parent_span_id": parent_span_id,
        "name": span.name,
        "start_time": _ns_to_iso(span.start_time),
        "end_time": _ns_to_iso(span.end_time),
        "status": span.status.status_code.name,
        "attributes": dict(span.attributes or {}),
    }


class ObservationStoreExporter(SpanExporter):
    """A real OTel SpanExporter (same interface as ConsoleSpanExporter /
    InMemorySpanExporter) that pushes every finished span through the
    Privacy Gate and into the Event Store.

    Scoping decision, stated plainly: this plugs in at the OTel SDK level
    (agent-runtime's own TracerProvider), not by parsing the standalone
    Collector's OTLP wire output. Hand-parsing real OTLP JSON/protobuf
    correctly (base64 trace/span IDs, nanosecond timestamps, typed
    attribute values) is a meaningfully bigger and more error-prone task
    than this step needs. The standalone Collector (Step 32) remains real
    and useful for feeding OTHER external tools; this is a second,
    independent path straight into our own Event Store."""

    def __init__(self, database_url: str) -> None:
        self._database_url = database_url

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        conn = psycopg.connect(self._database_url)
        try:
            for span in spans:
                raw = _span_to_raw_dict(span)
                event = apply_privacy_gate(raw)
                store_event(conn, event)
        except Exception:
            return SpanExportResult.FAILURE
        finally:
            conn.close()
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        pass
