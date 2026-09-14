from __future__ import annotations

import psycopg


class StaleStateVersion(Exception):
    def __init__(self, expected: int, actual: int) -> None:
        self.expected = expected
        self.actual = actual
        super().__init__(f"expected_state_version {expected} does not match current {actual}")


def check_and_advance_state_version(conn: psycopg.Connection, agent_id: str, expected_state_version: int) -> None:
    """Optimistic concurrency check (CLAUDE.md "stale browser state"
    failure mode). Must run in the SAME transaction as the ledger/outbox
    write — otherwise two concurrent requests could both read the same
    "current" version before either updates it, and both would pass.

    Known simplification: this table tracks state_version as last
    ACCEPTED BY THE API, not confirmed-applied by the real agent runtime.
    Reconciliation (a later step) is what corrects this once the
    dispatcher/heartbeat pipeline exists.
    """
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO agent_state (agent_id) VALUES (%s) ON CONFLICT (agent_id) DO NOTHING",
            (agent_id,),
        )
        # FOR UPDATE locks this row for the rest of the transaction, so a
        # second concurrent request for the same agent has to wait its
        # turn instead of also reading the pre-update value.
        cur.execute("SELECT state_version FROM agent_state WHERE agent_id = %s FOR UPDATE", (agent_id,))
        (current,) = cur.fetchone()

        if current != expected_state_version:
            raise StaleStateVersion(expected_state_version, current)

        cur.execute(
            "UPDATE agent_state SET state_version = state_version + 1, updated_at = now() WHERE agent_id = %s",
            (agent_id,),
        )
