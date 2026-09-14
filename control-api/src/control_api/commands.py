from __future__ import annotations

import uuid

import psycopg

from .db import record_command
from .policy import check_and_advance_state_version


def submit_command(
    conn: psycopg.Connection,
    *,
    agent_id: str,
    action: str,
    expected_state_version: int,
    reason: str,
) -> str:
    """One atomic unit: check the state_version policy AND record the
    command, or neither happens. Raises StaleStateVersion (from policy.py)
    if the check fails — the caller decides how to turn that into an HTTP
    response. Returns the generated command_id on success."""
    command_id = f"cmd_{uuid.uuid4().hex}"
    with conn.transaction():
        check_and_advance_state_version(conn, agent_id, expected_state_version)
        record_command(
            conn,
            command_id=command_id,
            agent_id=agent_id,
            action=action,
            expected_state_version=expected_state_version,
            reason=reason,
        )
    return command_id
