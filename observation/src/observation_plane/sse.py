from __future__ import annotations

import asyncio
import json
import time
from typing import AsyncIterator

import psycopg


async def stream_events(
    database_url: str,
    after_event_id: int,
    poll_interval_seconds: float = 0.5,
    max_duration_seconds: float = 3600.0,
) -> AsyncIterator[str]:
    """Yields SSE-formatted messages for every observation_event with
    event_id > after_event_id, in order, until max_duration_seconds
    passes (bounded so this is testable, and so a connection eventually
    recycles instead of staying open forever).

    Each message's `id:` field is the event_id — a reconnecting client
    sends that back as the Last-Event-ID header, and we resume exactly
    there. No gaps, no repeats, regardless of how long the client was
    disconnected."""
    conn = psycopg.connect(database_url)
    try:
        deadline = time.monotonic() + max_duration_seconds
        last_seen = after_event_id

        while time.monotonic() < deadline:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT event_id, trace_id, name, status, attributes
                    FROM observation_events
                    WHERE event_id > %s
                    ORDER BY event_id
                    LIMIT 100
                    """,
                    (last_seen,),
                )
                rows = cur.fetchall()

            for event_id, trace_id, name, status, attributes in rows:
                payload = {"trace_id": trace_id, "name": name, "status": status, "attributes": attributes}
                yield f"id: {event_id}\ndata: {json.dumps(payload)}\n\n"
                last_seen = event_id

            if not rows:
                await asyncio.sleep(poll_interval_seconds)
    finally:
        conn.close()
