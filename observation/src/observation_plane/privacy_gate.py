from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# The Observation Plane must never leak more than execution shape/status.
# Only these attribute keys are ever allowed through — anything else is
# dropped, never passed through "just in case it's useful later."
ALLOWED_ATTRIBUTE_KEYS = {
    "run_id",
    "agent_name",
    "run.status",
    "resumed",
    "step_name",
    "step_id",
}

# Applied to the VALUE of every allowed string attribute, in case sensitive
# data ends up inside an otherwise-legitimate field (e.g. a customer email
# accidentally embedded in agent_name).
_REDACTION_PATTERNS = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[REDACTED_EMAIL]"),
    (re.compile(r"\bsk-[A-Za-z0-9]{16,}\b"), "[REDACTED_SECRET]"),
    (re.compile(r"\b\d{13,16}\b"), "[REDACTED_NUMBER]"),  # credit-card-shaped digit runs
]


@dataclass(frozen=True)
class ObservationEvent:
    """The normalized, safe-to-store shape — what the Event Store (Step 34)
    actually persists. Never the raw span; always gate output."""

    trace_id: str
    span_id: str
    parent_span_id: str | None
    name: str
    start_time: str
    end_time: str
    status: str
    attributes: dict[str, Any] = field(default_factory=dict)


def _redact(value: str) -> str:
    for pattern, replacement in _REDACTION_PATTERNS:
        value = pattern.sub(replacement, value)
    return value


def _clean_attributes(raw_attributes: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in raw_attributes.items():
        if key not in ALLOWED_ATTRIBUTE_KEYS:
            continue  # not on the allowlist — silently dropped, not stored
        if isinstance(value, str):
            value = _redact(value)
        cleaned[key] = value
    return cleaned


def apply_privacy_gate(raw_span: dict[str, Any]) -> ObservationEvent:
    """Takes a raw span-like dict (as received from the OTel Collector) and
    returns the allowlisted, redacted, normalized event that's safe to
    persist — "allowlist, redact, normalize" from the architecture diagram."""
    return ObservationEvent(
        trace_id=raw_span["trace_id"],
        span_id=raw_span["span_id"],
        parent_span_id=raw_span.get("parent_span_id"),
        name=raw_span["name"],
        start_time=raw_span["start_time"],
        end_time=raw_span["end_time"],
        status=raw_span.get("status", "UNSET"),
        attributes=_clean_attributes(raw_span.get("attributes", {})),
    )
