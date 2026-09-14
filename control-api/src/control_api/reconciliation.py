from __future__ import annotations

from dataclasses import dataclass

import psycopg


@dataclass(frozen=True)
class ExpiredCommand:
    command_id: str
    agent_id: str


def expire_stale_deliveries(conn: psycopg.Connection, max_age_seconds: float) -> list[ExpiredCommand]:
    """Finds commands DELIVERED more than max_age_seconds ago that never
    got any terminal ack, and marks them EXPIRED.

    CLAUDE.md section 14: "Adapter offline: command remains queued until
    TTL; never mark applied." This is what enforces that TTL — a command
    an offline/crashed adapter never acked does not stay ambiguous
    forever; it becomes an honest EXPIRED, never a guessed APPLIED.

    Known simplification: this only checks elapsed time, not a live
    heartbeat comparison — we don't yet have agents heartbeating INTO the
    Control API (that's a later piece). Good enough to stop a command
    from being stuck in limbo forever."""
    expired: list[ExpiredCommand] = []
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT command_id, agent_id, action, expected_state_version, reason
                FROM command_ledger
                WHERE event_type = 'DELIVERED'
                  AND recorded_at < now() - (%s::text || ' seconds')::interval
                  AND command_id NOT IN (
                      SELECT command_id FROM command_ledger
                      WHERE event_type IN ('APPLIED', 'FAILED', 'REJECTED', 'UNSUPPORTED', 'EXPIRED')
                  )
                """,
                (max_age_seconds,),
            )
            stale_commands = cur.fetchall()

            for command_id, agent_id, action, expected_state_version, reason in stale_commands:
                cur.execute(
                    """
                    INSERT INTO command_ledger
                        (command_id, event_type, agent_id, action, expected_state_version, reason)
                    VALUES (%s, 'EXPIRED', %s, %s, %s, %s)
                    """,
                    (command_id, agent_id, action, expected_state_version, reason),
                )
                expired.append(ExpiredCommand(command_id=command_id, agent_id=agent_id))

    return expired
