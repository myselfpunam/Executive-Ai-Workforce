from __future__ import annotations

import psycopg


def record_command(
    conn: psycopg.Connection,
    *,
    command_id: str,
    agent_id: str,
    action: str,
    expected_state_version: int,
    reason: str,
) -> None:
    """Writes the initial REQUESTED ledger event AND the outbox row.

    Deliberately does NOT open its own transaction — the caller decides the
    transaction boundary, because this often needs to run alongside other
    checks (e.g. the policy engine's state_version check, see policy.py)
    as one atomic unit. Either everything in the caller's transaction is
    recorded, or none of it is."""
    conn.execute(
        """
        INSERT INTO command_ledger
            (command_id, event_type, agent_id, action, expected_state_version, reason)
        VALUES (%s, 'REQUESTED', %s, %s, %s, %s)
        """,
        (command_id, agent_id, action, expected_state_version, reason),
    )
    conn.execute(
        """
        INSERT INTO command_outbox
            (command_id, agent_id, action, expected_state_version, reason)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (command_id, agent_id, action, expected_state_version, reason),
    )
