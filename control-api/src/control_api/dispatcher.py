from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

import psycopg


@dataclass(frozen=True)
class ClaimedCommand:
    command_id: str
    agent_id: str
    action: str
    expected_state_version: int
    reason: str


def claim_next_command(conn: psycopg.Connection, agent_id: str) -> ClaimedCommand | None:
    """Finds the oldest still-PENDING command for this agent and marks it
    DISPATCHED, atomically. Returns None if there's nothing pending.

    FOR UPDATE SKIP LOCKED is the standard Postgres pattern for a work
    queue: if another concurrent call already has a lock on a row, this
    one skips it instead of waiting — so two callers can never walk away
    with the same command_id (proven in test_dispatcher.py with real
    concurrent threads, not just sequential calls)."""
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT command_id, agent_id, action, expected_state_version, reason
                FROM command_outbox
                WHERE agent_id = %s AND status = 'PENDING'
                ORDER BY created_at
                LIMIT 1
                FOR UPDATE SKIP LOCKED
                """,
                (agent_id,),
            )
            row = cur.fetchone()
            if row is None:
                return None

            command_id, claimed_agent_id, action, expected_state_version, reason = row
            cur.execute(
                "UPDATE command_outbox SET status = 'DISPATCHED', dispatched_at = now() WHERE command_id = %s",
                (command_id,),
            )
            # DELIVERED joins the ledger in the SAME transaction as the
            # outbox status change — the permanent history and the working
            # queue move together, same principle as Step 20's outbox write.
            cur.execute(
                """
                INSERT INTO command_ledger
                    (command_id, event_type, agent_id, action, expected_state_version, reason)
                VALUES (%s, 'DELIVERED', %s, %s, %s, %s)
                """,
                (command_id, claimed_agent_id, action, expected_state_version, reason),
            )

    return ClaimedCommand(command_id, claimed_agent_id, action, expected_state_version, reason)


async def wait_for_command(
    conn: psycopg.Connection,
    agent_id: str,
    timeout_seconds: float = 20.0,
    poll_interval_seconds: float = 0.5,
) -> ClaimedCommand | None:
    """Long-poll: hold the request open, checking the outbox periodically,
    until either a command shows up or timeout_seconds passes — instead of
    the adapter hammering this endpoint every second.

    Known simplification: this uses a plain (blocking) psycopg connection
    inside an async function, sleeping between checks with asyncio.sleep.
    Fine at this scale/learning stage; a production version with many
    concurrent long-polling agents would use an async DB driver instead so
    the DB call itself never blocks the event loop."""
    deadline = time.monotonic() + timeout_seconds
    while True:
        claimed = claim_next_command(conn, agent_id)
        if claimed is not None:
            return claimed
        if time.monotonic() >= deadline:
            return None
        await asyncio.sleep(poll_interval_seconds)
