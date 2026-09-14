from __future__ import annotations

import os
from dataclasses import asdict

import psycopg
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

from .projection import project_run
from .sse import stream_events

app = FastAPI(title="Observation API")


@app.get("/observation/v1/runs/{trace_id}")
async def get_run(trace_id: str) -> JSONResponse:
    conn = psycopg.connect(os.environ["DATABASE_URL"])
    try:
        projection = project_run(conn, trace_id)
    finally:
        conn.close()

    if projection is None:
        return JSONResponse(
            status_code=404,
            content={"code": "UNKNOWN_TRACE", "message": f"no run found for trace_id {trace_id}"},
        )

    return JSONResponse(status_code=200, content=asdict(projection))


@app.get("/observation/v1/events/stream")
async def stream(
    request: Request,
    poll_interval_seconds: float = 0.5,
    max_duration_seconds: float = 3600.0,
) -> StreamingResponse:
    """A browser (EventSource) connects here. On a fresh connection
    (no Last-Event-ID), we only stream NEW events from this moment on —
    not the entire history. On a reconnect, the browser automatically
    sends back the last id: it saw, and we resume exactly there."""
    last_event_id_header = request.headers.get("last-event-id")

    if last_event_id_header is not None:
        after_event_id = int(last_event_id_header)
    else:
        conn = psycopg.connect(os.environ["DATABASE_URL"])
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COALESCE(max(event_id), 0) FROM observation_events")
                (after_event_id,) = cur.fetchone()
        finally:
            conn.close()

    generator = stream_events(
        os.environ["DATABASE_URL"],
        after_event_id=after_event_id,
        poll_interval_seconds=poll_interval_seconds,
        max_duration_seconds=max_duration_seconds,
    )
    return StreamingResponse(generator, media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8001)
