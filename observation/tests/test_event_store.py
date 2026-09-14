import uuid

from observation_plane.event_store import compute_evidence_hash, store_event, verify_chain_integrity
from observation_plane.privacy_gate import ObservationEvent


def _event(**overrides) -> ObservationEvent:
    defaults = dict(
        trace_id=uuid.uuid4().hex,
        span_id=uuid.uuid4().hex[:16],
        parent_span_id=None,
        name="agent.step",
        start_time="2026-09-14T15:00:00Z",
        end_time="2026-09-14T15:00:01Z",
        status="UNSET",
        attributes={"run_id": "run_abc"},
    )
    defaults.update(overrides)
    return ObservationEvent(**defaults)


def test_storing_an_event_returns_a_hash_matching_a_fresh_recomputation(pg_conn):
    event = _event()

    stored_hash = store_event(pg_conn, event)

    with pg_conn.cursor() as cur:
        cur.execute(
            "SELECT previous_hash FROM observation_events WHERE evidence_hash = %s",
            (stored_hash,),
        )
        (previous_hash,) = cur.fetchone()

    assert stored_hash == compute_evidence_hash(event, previous_hash)


def test_events_chain_to_the_previous_events_hash(pg_conn):
    first_hash = store_event(pg_conn, _event())
    second_hash = store_event(pg_conn, _event())

    with pg_conn.cursor() as cur:
        cur.execute("SELECT previous_hash FROM observation_events WHERE evidence_hash = %s", (second_hash,))
        (second_previous_hash,) = cur.fetchone()

    assert second_previous_hash == first_hash
    assert first_hash != second_hash


def test_verify_chain_integrity_is_true_for_an_untampered_chain(pg_conn):
    store_event(pg_conn, _event())
    store_event(pg_conn, _event())

    assert verify_chain_integrity(pg_conn) is True


def test_verify_chain_integrity_catches_a_row_tampered_with_directly(pg_conn, superuser_conn):
    event = _event(attributes={"run_id": "run_original"})
    stored_hash = store_event(pg_conn, event)  # committed normally — a real, valid event

    # Simulate an attacker/operator with elevated access bypassing the
    # append-only trigger entirely — this is exactly the scenario the hash
    # chain exists for; the trigger alone cannot stop a superuser.
    #
    # Deliberately NOT committed: both the trigger-disable (transactional
    # DDL in Postgres) and the tampering UPDATE are rolled back at the end,
    # so this test proves detection without permanently corrupting the
    # shared dev database for every test run after it.
    superuser_conn.execute("ALTER TABLE observation_events DISABLE TRIGGER observation_events_no_update")
    superuser_conn.execute(
        "UPDATE observation_events SET attributes = '{\"run_id\": \"run_tampered\"}'::jsonb WHERE evidence_hash = %s",
        (stored_hash,),
    )

    # Check on the SAME connection/transaction, so it sees the not-yet-
    # committed tamper — a different connection (like pg_conn) never would.
    integrity_ok = verify_chain_integrity(superuser_conn)

    superuser_conn.rollback()

    assert integrity_ok is False
