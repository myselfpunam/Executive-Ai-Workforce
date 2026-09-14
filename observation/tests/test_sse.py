import asyncio
import uuid

from observation_plane.event_store import store_event
from observation_plane.privacy_gate import ObservationEvent
from observation_plane.sse import stream_events


async def _collect_n(agen, n):
    items = []
    async for item in agen:
        items.append(item)
        if len(items) == n:
            break
    return items


async def _collect_all(agen):
    return [item async for item in agen]


def _latest_event_id(pg_conn) -> int:
    with pg_conn.cursor() as cur:
        cur.execute("SELECT COALESCE(max(event_id), 0) FROM observation_events")
        (value,) = cur.fetchone()
    return value


def _make_event(**overrides) -> ObservationEvent:
    defaults = dict(
        trace_id=uuid.uuid4().hex,
        span_id=uuid.uuid4().hex[:16],
        parent_span_id=None,
        name="agent.step",
        start_time="2026-09-14T15:00:00",
        end_time="2026-09-14T15:00:01",
        status="UNSET",
        attributes={"step_name": "retrieval"},
    )
    defaults.update(overrides)
    return ObservationEvent(**defaults)


def test_stream_yields_an_event_created_after_the_baseline(pg_conn, database_url):
    baseline = _latest_event_id(pg_conn)
    store_event(pg_conn, _make_event())

    agen = stream_events(database_url, after_event_id=baseline, poll_interval_seconds=0.05, max_duration_seconds=5)
    messages = asyncio.run(_collect_n(agen, 1))

    assert len(messages) == 1
    assert messages[0].startswith("id: ")
    assert "retrieval" in messages[0]


def test_stream_does_not_replay_events_at_or_before_the_baseline(pg_conn, database_url):
    store_event(pg_conn, _make_event(attributes={"step_name": "old-event"}))
    baseline = _latest_event_id(pg_conn)  # baseline is AFTER the event above
    store_event(pg_conn, _make_event(attributes={"step_name": "new-event"}))

    agen = stream_events(database_url, after_event_id=baseline, poll_interval_seconds=0.05, max_duration_seconds=1)
    messages = asyncio.run(_collect_all(agen))

    assert len(messages) == 1
    assert "new-event" in messages[0]
    assert "old-event" not in messages[0]


def test_stream_times_out_with_no_messages_when_nothing_new_arrives(pg_conn, database_url):
    baseline = _latest_event_id(pg_conn)  # nothing will be stored after this

    agen = stream_events(database_url, after_event_id=baseline, poll_interval_seconds=0.05, max_duration_seconds=0.3)
    messages = asyncio.run(_collect_all(agen))

    assert messages == []


def test_reconnecting_with_the_last_seen_id_resumes_without_gaps_or_repeats(pg_conn, database_url):
    baseline = _latest_event_id(pg_conn)
    store_event(pg_conn, _make_event(attributes={"step_name": "first"}))
    store_event(pg_conn, _make_event(attributes={"step_name": "second"}))

    # "first connection": only catches the first event, then disconnects
    first_agen = stream_events(database_url, after_event_id=baseline, poll_interval_seconds=0.05, max_duration_seconds=5)
    first_messages = asyncio.run(_collect_n(first_agen, 1))
    assert "first" in first_messages[0]

    last_seen_id = int(first_messages[0].split("\n")[0].removeprefix("id: "))

    # "reconnect" using that id as Last-Event-ID — must pick up exactly the
    # second event, not repeat the first, not miss anything.
    second_agen = stream_events(database_url, after_event_id=last_seen_id, poll_interval_seconds=0.05, max_duration_seconds=1)
    second_messages = asyncio.run(_collect_all(second_agen))

    assert len(second_messages) == 1
    assert "second" in second_messages[0]
