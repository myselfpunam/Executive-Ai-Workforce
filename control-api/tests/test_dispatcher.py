import os
import threading
import uuid

import psycopg

from control_api.dispatcher import claim_next_command


def _fresh_agent_id() -> str:
    return f"agent_{uuid.uuid4().hex[:8]}"


def _seed_pending_command(conn, agent_id, command_id=None, action="PAUSE"):
    command_id = command_id or f"cmd_{uuid.uuid4().hex[:12]}"
    with conn.transaction():
        conn.execute(
            """
            INSERT INTO command_outbox (command_id, agent_id, action, expected_state_version, reason)
            VALUES (%s, %s, %s, 0, 'dispatcher test')
            """,
            (command_id, agent_id, action),
        )
    return command_id


def test_claims_the_only_pending_command_for_an_agent(pg_conn):
    agent_id = _fresh_agent_id()
    command_id = _seed_pending_command(pg_conn, agent_id)

    claimed = claim_next_command(pg_conn, agent_id)

    assert claimed is not None
    assert claimed.command_id == command_id
    assert claimed.agent_id == agent_id


def test_claiming_appends_a_delivered_event_to_the_ledger(pg_conn):
    agent_id = _fresh_agent_id()
    command_id = _seed_pending_command(pg_conn, agent_id)

    claim_next_command(pg_conn, agent_id)

    with pg_conn.cursor() as cur:
        cur.execute(
            "SELECT event_type FROM command_ledger WHERE command_id = %s ORDER BY ledger_id",
            (command_id,),
        )
        event_types = [row[0] for row in cur.fetchall()]

    assert event_types == ["DELIVERED"]  # this command was seeded directly into the outbox, skipping REQUESTED


def test_claiming_marks_the_row_dispatched_so_it_cannot_be_claimed_again(pg_conn):
    agent_id = _fresh_agent_id()
    _seed_pending_command(pg_conn, agent_id)

    first = claim_next_command(pg_conn, agent_id)
    second = claim_next_command(pg_conn, agent_id)

    assert first is not None
    assert second is None  # nothing left PENDING for this agent


def test_returns_none_when_nothing_is_pending_for_that_agent():
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        claimed = claim_next_command(conn, _fresh_agent_id())

    assert claimed is None


def test_claiming_for_one_agent_never_touches_another_agents_command(pg_conn):
    agent_a = _fresh_agent_id()
    agent_b = _fresh_agent_id()
    command_for_b = _seed_pending_command(pg_conn, agent_b)

    claimed_for_a = claim_next_command(pg_conn, agent_a)
    claimed_for_b = claim_next_command(pg_conn, agent_b)

    assert claimed_for_a is None
    assert claimed_for_b is not None
    assert claimed_for_b.command_id == command_for_b


def test_oldest_pending_command_is_claimed_first(pg_conn):
    agent_id = _fresh_agent_id()
    older = _seed_pending_command(pg_conn, agent_id)
    newer = _seed_pending_command(pg_conn, agent_id)

    first_claim = claim_next_command(pg_conn, agent_id)
    second_claim = claim_next_command(pg_conn, agent_id)

    assert first_claim.command_id == older
    assert second_claim.command_id == newer


def test_concurrent_claim_attempts_never_return_the_same_command():
    """The real point of FOR UPDATE SKIP LOCKED: fire several genuinely
    concurrent claim attempts (separate threads, separate connections) at
    ONE pending command and prove exactly one of them gets it — not zero,
    not two."""
    agent_id = _fresh_agent_id()
    setup_conn = psycopg.connect(os.environ["DATABASE_URL"])
    command_id = _seed_pending_command(setup_conn, agent_id)
    setup_conn.close()

    results: list = []
    results_lock = threading.Lock()

    def worker():
        conn = psycopg.connect(os.environ["DATABASE_URL"])
        try:
            claimed = claim_next_command(conn, agent_id)
            with results_lock:
                results.append(claimed)
        finally:
            conn.close()

    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    successful_claims = [r for r in results if r is not None]
    assert len(successful_claims) == 1
    assert successful_claims[0].command_id == command_id
