from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@dataclass(frozen=True)
class Event:
    """One structured, observable fact about a run. This shape is what the
    Observation Plane (Week 13-14) will eventually ingest — keep it
    JSON-serializable and self-contained, never a reference to live objects.
    """

    event_id: str
    run_id: str
    type: str
    occurred_at: str
    step_id: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def create(run_id: str, type: str, step_id: str | None = None, data: dict[str, Any] | None = None) -> "Event":
        return Event(
            event_id=new_id("evt"),
            run_id=run_id,
            type=type,
            occurred_at=datetime.now(timezone.utc).isoformat(),
            step_id=step_id,
            data=data or {},
        )
