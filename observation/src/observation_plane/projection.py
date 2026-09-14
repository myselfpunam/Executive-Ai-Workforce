from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import psycopg


@dataclass(frozen=True)
class RunProjection:
    """A dashboard-ready summary of one run, folded from many raw events.

    Known simplification: no cost or coverage fields — we don't have a
    real source for either yet (no token/dollar tracking, no defined
    "expected telemetry" baseline). Omitted honestly rather than
    fabricated as a placeholder zero.

    Also: a paused-then-resumed run currently produces TWO separate
    projections (one per trace_id) sharing the same run_id — our tracing
    doesn't yet connect a resume back to its original trace. Good enough
    for now; a future step could link them with OTel span Links."""

    run_id: str
    agent_name: str | None
    status: str | None
    step_count: int
    started_at: str
    ended_at: str
    duration_seconds: float


def project_run(conn: psycopg.Connection, trace_id: str) -> RunProjection | None:
    """Reads every raw event for one trace_id and folds them into one
    summary row. Returns None if there's no root "agent.run" span for
    this trace_id (nothing to project yet, or an unknown trace)."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT name, start_time, end_time, attributes FROM observation_events WHERE trace_id = %s ORDER BY event_id",
            (trace_id,),
        )
        rows = cur.fetchall()

    run_row = next((r for r in rows if r[0] == "agent.run"), None)
    if run_row is None:
        return None

    _, start_time, end_time, attributes = run_row
    step_count = sum(1 for r in rows if r[0] == "agent.step")

    start_dt = datetime.fromisoformat(start_time)
    end_dt = datetime.fromisoformat(end_time)

    return RunProjection(
        run_id=attributes.get("run_id", ""),
        agent_name=attributes.get("agent_name"),
        status=attributes.get("run.status"),
        step_count=step_count,
        started_at=start_time,
        ended_at=end_time,
        duration_seconds=(end_dt - start_dt).total_seconds(),
    )


def list_recent_runs(conn: psycopg.Connection, limit: int = 50) -> list[RunProjection]:
    """The dashboard's initial "give me the overview" snapshot — every
    other recent run, most recent first. Live updates after this initial
    load come from the SSE stream (Step 36), not from re-polling this."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT trace_id FROM observation_events
            WHERE name = 'agent.run'
            ORDER BY event_id DESC
            LIMIT %s
            """,
            (limit,),
        )
        trace_ids = [row[0] for row in cur.fetchall()]

    projections = []
    for trace_id in trace_ids:
        projection = project_run(conn, trace_id)
        if projection is not None:
            projections.append(projection)
    return projections
