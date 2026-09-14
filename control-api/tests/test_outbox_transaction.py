import uuid

import psycopg
import pytest

from control_api.db import record_command


def _count(conn, table, command_id) -> int:
    with conn.cursor() as cur:
        cur.execute(f"SELECT count(*) FROM {table} WHERE command_id = %s", (command_id,))
        return cur.fetchone()[0]


def test_recording_a_command_writes_both_ledger_and_outbox_atomically(pg_conn):
    command_id = f"cmd_{uuid.uuid4().hex[:12]}"

    # record_command no longer opens its own transaction (Step 22 needed it
    # to participate in a shared transaction with the policy check) — the
    # caller now owns the transaction boundary.
    with pg_conn.transaction():
        record_command(
            pg_conn,
            command_id=command_id,
            agent_id="agent_test",
            action="PAUSE",
            expected_state_version=1,
            reason="test: atomic write",
        )

    assert _count(pg_conn, "command_ledger", command_id) == 1
    assert _count(pg_conn, "command_outbox", command_id) == 1


def test_a_failure_partway_through_rolls_back_both_writes(pg_conn):
    command_id = f"cmd_{uuid.uuid4().hex[:12]}"

    with pytest.raises(psycopg.errors.CheckViolation):
        with pg_conn.transaction():
            pg_conn.execute(
                """
                INSERT INTO command_ledger
                    (command_id, event_type, agent_id, action, expected_state_version, reason)
                VALUES (%s, 'REQUESTED', %s, %s, %s, %s)
                """,
                (command_id, "agent_test", "PAUSE", 1, "this insert is valid"),
            )
            # Deliberately invalid action — violates the CHECK constraint,
            # forcing the whole transaction (including the valid insert
            # above) to roll back.
            pg_conn.execute(
                """
                INSERT INTO command_outbox
                    (command_id, agent_id, action, expected_state_version, reason)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (command_id, "agent_test", "DELETE_EVERYTHING", 1, "this insert is invalid"),
            )

    # The FIRST insert must not have survived either, even though it was
    # valid on its own — that's the whole point of one shared transaction.
    assert _count(pg_conn, "command_ledger", command_id) == 0
    assert _count(pg_conn, "command_outbox", command_id) == 0
