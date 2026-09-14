from __future__ import annotations

from dataclasses import dataclass

import psycopg
from psycopg.types.json import Json

TERMINAL_STATUSES = {"APPLIED", "FAILED", "REJECTED", "UNSUPPORTED"}


class UnknownCommand(Exception):
    pass


@dataclass(frozen=True)
class AckResult:
    command_id: str
    status: str
    already_processed: bool


def record_acknowledgement(
    conn: psycopg.Connection,
    *,
    agent_id: str,
    command_id: str,
    status: str,
    resulting_state: str,
    state_version: int,
) -> AckResult:
    """The adapter reporting back what actually happened. Idempotent: if
    this command already has a terminal event, a repeat ack (e.g. a
    retried network call) is recognized and NOT re-applied — CLAUDE.md
    section 14: "Duplicate delivery: previous result; one effect; one
    audit trail," the same principle as the SDK's CommandInbox, now
    enforced server-side too."""
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT event_type, agent_id, action, expected_state_version, reason
                FROM command_ledger WHERE command_id = %s ORDER BY ledger_id
                """,
                (command_id,),
            )
            rows = cur.fetchall()

            if not rows:
                raise UnknownCommand(f"no such command {command_id}")

            _, ledger_agent_id, action, expected_state_version, reason = rows[0]
            if ledger_agent_id != agent_id:
                raise UnknownCommand(f"command {command_id} does not belong to agent {agent_id}")

            already_terminal = [r[0] for r in rows if r[0] in TERMINAL_STATUSES]
            if already_terminal:
                return AckResult(command_id=command_id, status=already_terminal[-1], already_processed=True)

            cur.execute(
                """
                INSERT INTO command_ledger
                    (command_id, event_type, agent_id, action, expected_state_version, reason, detail)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    command_id,
                    status,
                    agent_id,
                    action,
                    expected_state_version,
                    reason,
                    Json({"resulting_state": resulting_state, "state_version": state_version}),
                ),
            )

            # Reconcile agent_state with the CONFIRMED real value — the
            # earlier optimistic bump (policy.py, at submission time) was
            # a guess; this is ground truth from the agent itself. If the
            # command actually failed, this corrects the version back.
            cur.execute(
                "UPDATE agent_state SET state_version = %s, updated_at = now() WHERE agent_id = %s",
                (state_version, agent_id),
            )

    return AckResult(command_id=command_id, status=status, already_processed=False)
