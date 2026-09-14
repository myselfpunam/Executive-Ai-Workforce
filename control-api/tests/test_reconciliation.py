import uuid

from control_api.reconciliation import expire_stale_deliveries


def _fresh_agent_id() -> str:
    return f"agent_{uuid.uuid4().hex[:8]}"


def _seed_delivered_command(conn, agent_id, seconds_ago: float) -> str:
    command_id = f"cmd_{uuid.uuid4().hex[:12]}"
    with conn.transaction():
        conn.execute(
            """
            INSERT INTO command_ledger
                (command_id, event_type, agent_id, action, expected_state_version, reason, recorded_at)
            VALUES (%s, 'DELIVERED', %s, 'PAUSE', 0, 'reconciliation test', now() - (%s::text || ' seconds')::interval)
            """,
            (command_id, agent_id, seconds_ago),
        )
    return command_id


def _event_types(conn, command_id) -> list[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT event_type FROM command_ledger WHERE command_id = %s ORDER BY ledger_id", (command_id,))
        return [row[0] for row in cur.fetchall()]


def test_a_stale_delivered_command_is_marked_expired(pg_conn):
    agent_id = _fresh_agent_id()
    command_id = _seed_delivered_command(pg_conn, agent_id, seconds_ago=100)

    expired = expire_stale_deliveries(pg_conn, max_age_seconds=30)

    assert any(e.command_id == command_id for e in expired)
    assert _event_types(pg_conn, command_id) == ["DELIVERED", "EXPIRED"]


def test_a_recently_delivered_command_is_not_expired_yet(pg_conn):
    agent_id = _fresh_agent_id()
    command_id = _seed_delivered_command(pg_conn, agent_id, seconds_ago=1)

    expired = expire_stale_deliveries(pg_conn, max_age_seconds=30)

    assert not any(e.command_id == command_id for e in expired)
    assert _event_types(pg_conn, command_id) == ["DELIVERED"]


def test_an_already_acked_command_is_never_touched(pg_conn):
    agent_id = _fresh_agent_id()
    command_id = _seed_delivered_command(pg_conn, agent_id, seconds_ago=100)
    with pg_conn.transaction():
        pg_conn.execute(
            """
            INSERT INTO command_ledger (command_id, event_type, agent_id, action, expected_state_version, reason)
            VALUES (%s, 'APPLIED', %s, 'PAUSE', 0, 'already handled')
            """,
            (command_id, agent_id),
        )

    expired = expire_stale_deliveries(pg_conn, max_age_seconds=30)

    assert not any(e.command_id == command_id for e in expired)
    assert _event_types(pg_conn, command_id) == ["DELIVERED", "APPLIED"]


def test_running_reconciliation_twice_does_not_double_expire(pg_conn):
    agent_id = _fresh_agent_id()
    command_id = _seed_delivered_command(pg_conn, agent_id, seconds_ago=100)

    expire_stale_deliveries(pg_conn, max_age_seconds=30)
    expire_stale_deliveries(pg_conn, max_age_seconds=30)

    assert _event_types(pg_conn, command_id) == ["DELIVERED", "EXPIRED"]
