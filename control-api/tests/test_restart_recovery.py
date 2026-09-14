import os
import uuid

import psycopg
from fastapi.testclient import TestClient

from control_api.ack import record_acknowledgement
from control_api.app import app
from control_api.dispatcher import claim_next_command

client = TestClient(app)


def _fresh_agent_id() -> str:
    return f"agent_{uuid.uuid4().hex[:8]}"


def test_a_pending_command_is_still_visible_from_a_totally_new_connection():
    agent_id = _fresh_agent_id()
    submitted = client.post(
        f"/control/v1/agents/{agent_id}/commands",
        json={"action": "PAUSE", "expected_state_version": 0, "reason": "restart test"},
    )
    command_id = submitted.json()["command_id"]

    # A brand-new connection, opened fresh — nothing here shares any
    # Python object with the request that submitted the command above.
    fresh_conn = psycopg.connect(os.environ["DATABASE_URL"])
    try:
        with fresh_conn.cursor() as cur:
            cur.execute("SELECT status FROM command_outbox WHERE command_id = %s", (command_id,))
            (status,) = cur.fetchone()
    finally:
        fresh_conn.close()

    assert status == "PENDING"


def test_a_queued_command_survives_a_simulated_restart_and_completes_end_to_end():
    """Nothing about correctness here may depend on a Python process
    staying alive — everything must be recoverable from Postgres alone.
    Proven by using a SEPARATE, independent connection for each phase
    below, exactly as a freshly-restarted process would have to."""
    agent_id = _fresh_agent_id()

    # --- "process 1": accepts the command, then imagine it crashes ---
    submitted = client.post(
        f"/control/v1/agents/{agent_id}/commands",
        json={"action": "PAUSE", "expected_state_version": 0, "reason": "restart recovery test"},
    )
    command_id = submitted.json()["command_id"]

    # --- "process 2" (after restart): fresh connection, claims + acks ---
    conn_after_restart = psycopg.connect(os.environ["DATABASE_URL"])
    try:
        claimed = claim_next_command(conn_after_restart, agent_id)
        assert claimed is not None
        assert claimed.command_id == command_id

        result = record_acknowledgement(
            conn_after_restart,
            agent_id=agent_id,
            command_id=command_id,
            status="APPLIED",
            resulting_state="PAUSED",
            state_version=1,
        )
        assert result.already_processed is False
    finally:
        conn_after_restart.close()

    # --- "process 3": yet another fresh connection, just to verify ---
    conn_verify = psycopg.connect(os.environ["DATABASE_URL"])
    try:
        with conn_verify.cursor() as cur:
            cur.execute(
                "SELECT event_type FROM command_ledger WHERE command_id = %s ORDER BY ledger_id",
                (command_id,),
            )
            event_types = [row[0] for row in cur.fetchall()]
    finally:
        conn_verify.close()

    assert event_types == ["REQUESTED", "DELIVERED", "APPLIED"]
