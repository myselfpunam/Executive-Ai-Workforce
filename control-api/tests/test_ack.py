import uuid

from fastapi.testclient import TestClient

from control_api.app import app

client = TestClient(app)


def _fresh_agent_id() -> str:
    return f"agent_{uuid.uuid4().hex[:8]}"


def _submit_and_deliver(agent_id: str) -> str:
    """Walks a command through submit + poll, exactly like a real adapter
    would, and returns its command_id."""
    submitted = client.post(
        f"/control/v1/agents/{agent_id}/commands",
        json={"action": "PAUSE", "expected_state_version": 0, "reason": "ack test"},
    )
    command_id = submitted.json()["command_id"]

    polled = client.get(f"/control/v1/agents/{agent_id}/commands/poll?timeout_seconds=2&poll_interval_seconds=0.05")
    assert polled.json()["command"]["command_id"] == command_id

    return command_id


def _ack_url(agent_id: str, command_id: str) -> str:
    return f"/control/v1/agents/{agent_id}/commands/{command_id}/ack"


def test_acking_applied_completes_the_ledger_lifecycle(pg_conn):
    agent_id = _fresh_agent_id()
    command_id = _submit_and_deliver(agent_id)

    response = client.post(_ack_url(agent_id, command_id), json={"status": "APPLIED", "resulting_state": "PAUSED", "state_version": 1})

    assert response.status_code == 200
    assert response.json() == {"command_id": command_id, "status": "APPLIED", "already_processed": False}

    with pg_conn.cursor() as cur:
        cur.execute("SELECT event_type FROM command_ledger WHERE command_id = %s ORDER BY ledger_id", (command_id,))
        event_types = [r[0] for r in cur.fetchall()]

    assert event_types == ["REQUESTED", "DELIVERED", "APPLIED"]


def test_a_duplicate_ack_is_idempotent_and_does_not_add_a_second_ledger_row(pg_conn):
    agent_id = _fresh_agent_id()
    command_id = _submit_and_deliver(agent_id)

    first = client.post(_ack_url(agent_id, command_id), json={"status": "APPLIED", "resulting_state": "PAUSED", "state_version": 1})
    second = client.post(_ack_url(agent_id, command_id), json={"status": "APPLIED", "resulting_state": "PAUSED", "state_version": 1})

    assert first.json()["already_processed"] is False
    assert second.json()["already_processed"] is True

    with pg_conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM command_ledger WHERE command_id = %s AND event_type = 'APPLIED'", (command_id,))
        applied_count = cur.fetchone()[0]

    assert applied_count == 1


def test_ack_for_an_unknown_command_returns_404():
    response = client.post(
        _ack_url(_fresh_agent_id(), "cmd_does_not_exist"),
        json={"status": "APPLIED", "resulting_state": "PAUSED", "state_version": 1},
    )

    assert response.status_code == 404
    assert response.json()["code"] == "UNKNOWN_COMMAND"


def test_ack_with_an_invalid_status_is_rejected_with_400():
    agent_id = _fresh_agent_id()
    command_id = _submit_and_deliver(agent_id)

    response = client.post(_ack_url(agent_id, command_id), json={"status": "MADE_UP_STATUS", "resulting_state": "PAUSED", "state_version": 1})

    assert response.status_code == 400
    assert response.json()["code"] == "SCHEMA_VALIDATION_FAILED"


def test_a_failed_command_corrects_agent_state_version_back_instead_of_keeping_the_optimistic_guess(pg_conn):
    agent_id = _fresh_agent_id()
    command_id = _submit_and_deliver(agent_id)  # policy.py optimistically bumped agent_state to version 1

    # The agent actually failed to apply it — state never really moved.
    response = client.post(_ack_url(agent_id, command_id), json={"status": "FAILED", "resulting_state": "ACTIVE", "state_version": 0})

    assert response.status_code == 200

    with pg_conn.cursor() as cur:
        cur.execute("SELECT state_version FROM agent_state WHERE agent_id = %s", (agent_id,))
        (current_version,) = cur.fetchone()

    assert current_version == 0  # corrected back to reality, not left at the wrong optimistic guess of 1
