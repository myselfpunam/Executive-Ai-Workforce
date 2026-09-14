import uuid

from fastapi.testclient import TestClient

from observation_plane.app import app
from observation_plane.event_store import store_event
from observation_plane.privacy_gate import ObservationEvent

client = TestClient(app)


def _seed_completed_run(conn, trace_id, run_id):
    root_span_id = uuid.uuid4().hex[:16]
    store_event(
        conn,
        ObservationEvent(
            trace_id=trace_id,
            span_id=uuid.uuid4().hex[:16],
            parent_span_id=root_span_id,
            name="agent.step",
            start_time="2026-09-14T15:00:00",
            end_time="2026-09-14T15:00:00.4",
            status="UNSET",
            attributes={"step_name": "retrieval"},
        ),
    )
    store_event(
        conn,
        ObservationEvent(
            trace_id=trace_id,
            span_id=root_span_id,
            parent_span_id=None,
            name="agent.run",
            start_time="2026-09-14T15:00:00",
            end_time="2026-09-14T15:00:01",
            status="UNSET",
            attributes={"run_id": run_id, "agent_name": "Sales Research Agent", "run.status": "COMPLETED"},
        ),
    )


def test_get_run_returns_the_projection_for_a_known_trace(pg_conn):
    trace_id = uuid.uuid4().hex
    run_id = f"run_{uuid.uuid4().hex[:8]}"
    _seed_completed_run(pg_conn, trace_id, run_id)

    response = client.get(f"/observation/v1/runs/{trace_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == run_id
    assert body["status"] == "COMPLETED"
    assert body["step_count"] == 1


def test_get_recent_runs_includes_a_freshly_seeded_run(pg_conn):
    trace_id = uuid.uuid4().hex
    run_id = f"run_{uuid.uuid4().hex[:8]}"
    _seed_completed_run(pg_conn, trace_id, run_id)

    response = client.get("/observation/v1/runs")

    assert response.status_code == 200
    run_ids = [r["run_id"] for r in response.json()]
    assert run_id in run_ids


def test_get_run_returns_404_for_an_unknown_trace():
    response = client.get(f"/observation/v1/runs/{uuid.uuid4().hex}")

    assert response.status_code == 404
    assert response.json()["code"] == "UNKNOWN_TRACE"


def test_a_fresh_connection_with_no_last_event_id_does_not_replay_old_history(pg_conn):
    # An event exists from BEFORE this connection — a fresh connection
    # (no Last-Event-ID) must not replay it, only genuinely new ones.
    store_event(
        pg_conn,
        ObservationEvent(
            trace_id=uuid.uuid4().hex,
            span_id=uuid.uuid4().hex[:16],
            parent_span_id=None,
            name="agent.step",
            start_time="2026-09-14T15:00:00",
            end_time="2026-09-14T15:00:00.1",
            status="UNSET",
            attributes={"step_name": "old-history"},
        ),
    )

    response = client.get(
        "/observation/v1/events/stream",
        params={"max_duration_seconds": 0.3, "poll_interval_seconds": 0.05},
    )

    assert response.status_code == 200
    assert response.text == ""


def test_stream_endpoint_honors_last_event_id_header_for_resumption(pg_conn):
    trace_id = uuid.uuid4().hex
    store_event(
        pg_conn,
        ObservationEvent(
            trace_id=trace_id,
            span_id=uuid.uuid4().hex[:16],
            parent_span_id=None,
            name="agent.step",
            start_time="2026-09-14T15:00:00",
            end_time="2026-09-14T15:00:00.1",
            status="UNSET",
            attributes={"step_name": "before-connect"},
        ),
    )
    with pg_conn.cursor() as cur:
        cur.execute("SELECT max(event_id) FROM observation_events")
        (existing_max,) = cur.fetchone()

    response = client.get(
        "/observation/v1/events/stream",
        params={"max_duration_seconds": 0.3, "poll_interval_seconds": 0.05},
        headers={"Last-Event-ID": str(existing_max - 1)},  # ask for everything after the second-to-last event
    )

    assert response.status_code == 200
    assert "before-connect" in response.text
